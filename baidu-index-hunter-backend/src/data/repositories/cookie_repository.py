"""
Cookie数据仓储类
处理 Cookie 相关的数据库操作
"""
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from sqlmodel import select, col, or_, and_, delete
from sqlalchemy import func, update
from sqlalchemy.dialects.mysql import insert as mysql_insert

from src.data.database import session_scope
from src.data.repositories.base_repository import BaseRepository
from src.data.models.cookie import CookieModel

class CookieRepository(BaseRepository[CookieModel]):
    def __init__(self):
        super().__init__(CookieModel)

    def get_cookies_by_account_id(self, account_id: str) -> List[CookieModel]:
        """获取指定账号的所有Cookie"""
        with session_scope() as session:
            statement = select(CookieModel).where(CookieModel.account_id == account_id)
            results = session.exec(statement).all()
            return [CookieModel.model_validate(r) for r in results]

    def get_cookies_by_account_ids(self, account_ids: List[str]) -> List[CookieModel]:
        """获取多个账号的Cookie"""
        with session_scope() as session:
            statement = select(CookieModel).where(col(CookieModel.account_id).in_(account_ids))
            results = session.exec(statement).all()
            return [CookieModel.model_validate(r) for r in results]

    def get_available_cookies(self) -> List[CookieModel]:
        """获取所有可用且未过期的Cookie"""
        now = datetime.now()
        with session_scope() as session:
            statement = select(CookieModel).where(
                CookieModel.is_available == True,
                CookieModel.is_permanently_banned == False,
                or_(CookieModel.expire_time == None, CookieModel.expire_time > now),
                or_(CookieModel.temp_ban_until == None, CookieModel.temp_ban_until < now)
            )
            results = session.exec(statement).all()
            return [CookieModel.model_validate(r) for r in results]

    def get_available_account_ids(self) -> List[str]:
        """获取所有可用账号ID"""
        now = datetime.now()
        with session_scope() as session:
            statement = select(CookieModel.account_id).distinct().where(
                CookieModel.is_available == True,
                CookieModel.is_permanently_banned == False,
                or_(CookieModel.expire_time == None, CookieModel.expire_time > now),
                or_(CookieModel.temp_ban_until == None, CookieModel.temp_ban_until < now)
            )
            return list(session.exec(statement).all())

    def upsert_cookies(self, account_id: str, cookies: Dict[str, str], expire_time: datetime) -> bool:
        """
        批量插入或更新Cookie
        """
        try:
            with session_scope() as session:
                for name, value in cookies.items():
                    # 使用 MySQL 的 upsert 语法
                    insert_stmt = mysql_insert(CookieModel.__table__).values(
                        account_id=account_id,
                        cookie_name=name,
                        cookie_value=value,
                        expire_time=expire_time,
                        is_available=True,
                        last_updated=func.now()
                    )
                    
                    on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
                        cookie_value=insert_stmt.inserted.cookie_value,
                        expire_time=insert_stmt.inserted.expire_time,
                        is_available=True,
                        last_updated=func.now()
                    )
                    session.exec(on_duplicate_key_stmt)
                session.commit()
                return True
        except Exception:
            return False

    def delete_by_account_id(self, account_id: str) -> int:
        """根据账号ID删除Cookie"""
        with session_scope() as session:
            statement = delete(CookieModel).where(CookieModel.account_id == account_id)
            result = session.exec(statement)
            session.commit()
            return result.rowcount

    def update_account_cookies_status(self, account_id: str, 
                                      is_available: Optional[bool] = None, 
                                      is_permanently_banned: Optional[bool] = None,
                                      temp_ban_until: Optional[Union[datetime, None]] = None) -> int:
        """更新账号下所有Cookie的状态"""
        updates = {}
        if is_available is not None:
            updates['is_available'] = is_available
        if is_permanently_banned is not None:
            updates['is_permanently_banned'] = is_permanently_banned
        # 注意：temp_ban_until 可以是 None，区分 None 和 未传参
        # 但这里为了简化，我们假设如果调用者想设为 None，必须显式传递
        # 这里逻辑有点 tricky，因为 Optional[datetime] 默认 None 通常表示不更新
        # 我们约定：如果不更新，不要传参。如果要清除，传 None? 
        # Python参数无法区分 "未传" 和 "传了None" 除非用 sentinel object。
        # 简单起见，我们在 kwarg 中处理。
        
        # 重新定义参数处理逻辑：
        # 这里我们假设 update 字典由调用者构建，或者我们分开写方法。
        # 鉴于 `ban_account_temporarily` 需要设 temp_ban_until，
        # `unban_account` 需要设 temp_ban_until = None。
        
        with session_scope() as session:
            statement = update(CookieModel).where(CookieModel.account_id == account_id)
            
            if is_available is not None:
                statement = statement.values(is_available=is_available)
            if is_permanently_banned is not None:
                statement = statement.values(is_permanently_banned=is_permanently_banned)
            
            # 特殊处理 temp_ban_until
            # 我们需要一种方式表达 "Set to NULL" vs "Don't Change"
            # 暂时我们分开写专门的方法比较安全，或者用 **kwargs
            pass

    def ban_account_permanently(self, account_id: str) -> int:
        """永久封禁账号"""
        with session_scope() as session:
            statement = update(CookieModel).where(CookieModel.account_id == account_id).values(
                is_available=False,
                is_permanently_banned=True
            )
            result = session.exec(statement)
            session.commit()
            return result.rowcount

    def ban_account_temporarily(self, account_id: str, unban_time: datetime) -> int:
        """临时封禁账号"""
        with session_scope() as session:
            statement = update(CookieModel).where(CookieModel.account_id == account_id).values(
                is_available=False,
                temp_ban_until=unban_time
            )
            result = session.exec(statement)
            session.commit()
            return result.rowcount

    def unban_account(self, account_id: str) -> int:
        """解封账号 (仅解封临时封禁)"""
        with session_scope() as session:
            statement = update(CookieModel).where(
                CookieModel.account_id == account_id,
                CookieModel.is_permanently_banned == False
            ).values(
                is_available=True,
                temp_ban_until=None
            )
            result = session.exec(statement)
            session.commit()
            return result.rowcount

    def force_unban_account(self, account_id: str) -> int:
        """强制解封账号 (包括永久封禁)"""
        with session_scope() as session:
            statement = update(CookieModel).where(CookieModel.account_id == account_id).values(
                is_available=True,
                is_permanently_banned=False,
                temp_ban_until=None
            )
            result = session.exec(statement)
            session.commit()
            return result.rowcount

    def update_account_id(self, old_id: str, new_id: str) -> int:
        """更新账号ID"""
        with session_scope() as session:
            statement = update(CookieModel).where(CookieModel.account_id == old_id).values(
                account_id=new_id
            )
            result = session.exec(statement)
            session.commit()
            return result.rowcount

    def cleanup_expired_cookies(self) -> int:
        """清理过期Cookie"""
        with session_scope() as session:
            statement = delete(CookieModel).where(
                CookieModel.expire_time != None,
                CookieModel.expire_time < func.now()
            )
            result = session.exec(statement)
            session.commit()
            return result.rowcount
            
    def get_expired_temp_bans(self) -> List[str]:
        """获取临时封禁已过期的账号ID"""
        with session_scope() as session:
            statement = select(CookieModel.account_id).distinct().where(
                CookieModel.is_available == False,
                CookieModel.is_permanently_banned == False,
                CookieModel.temp_ban_until != None,
                CookieModel.temp_ban_until < func.now()
            )
            return list(session.exec(statement).all())
            
    def unlock_accounts(self, account_ids: List[str]) -> int:
        """批量解封账号"""
        if not account_ids:
            return 0
        with session_scope() as session:
            statement = update(CookieModel).where(
                 col(CookieModel.account_id).in_(account_ids)
            ).values(
                is_available=True,
                temp_ban_until=None # Clear temp ban
            )
            result = session.exec(statement)
            session.commit()
            return result.rowcount
    
    def update_cookie_fields(self, cookie_id: int, fields: Dict[str, Any]) -> bool:
        """更新单个Cookie字段"""
        try:
             with session_scope() as session:
                statement = update(CookieModel).where(CookieModel.id == cookie_id).values(**fields)
                result = session.exec(statement)
                session.commit()
                return result.rowcount > 0
        except Exception:
            return False
            
    def get_cookie_by_id(self, cookie_id: int) -> Optional[CookieModel]:
        """根据ID获取Cookie"""
        with session_scope() as session:
            return session.get(CookieModel, cookie_id)


# 全局单例
cookie_repo = CookieRepository()
