"""
Cookie数据仓储类
处理 Cookie 相关的数据库操作
"""
from typing import List, Optional, Dict, Any, Union, Tuple
from datetime import datetime
from sqlmodel import select, col, or_, and_, delete, func
from sqlalchemy import update
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

    def get_account_ids_by_filter(self, 
                                 status: Optional[str] = None, 
                                 available_only: bool = False,
                                 account_id: Optional[str] = None) -> List[str]:
        """
        根据条件获取账号ID列表
        """
        now = datetime.now()
        with session_scope() as session:
            statement = select(CookieModel.account_id).distinct()
            
            if account_id:
                statement = statement.where(CookieModel.account_id == account_id)
            elif status:
                if status == 'perm_banned':
                    statement = statement.where(CookieModel.is_permanently_banned == True)
                elif status == 'temp_banned':
                    statement = statement.where(
                        CookieModel.temp_ban_until != None,
                        CookieModel.temp_ban_until > now,
                        CookieModel.is_permanently_banned == False
                    )
                elif status == 'expired':
                    statement = statement.where(
                        CookieModel.expire_time != None,
                        CookieModel.expire_time < now
                    )
                elif status == 'available':
                    statement = statement.where(
                        CookieModel.is_available == True,
                        or_(CookieModel.expire_time == None, CookieModel.expire_time >= now),
                        or_(CookieModel.temp_ban_until == None, CookieModel.temp_ban_until <= now),
                        CookieModel.is_permanently_banned == False
                    )
            elif available_only:
                 statement = statement.where(
                    CookieModel.is_available == True,
                    or_(CookieModel.expire_time == None, CookieModel.expire_time > now),
                    or_(CookieModel.temp_ban_until == None, CookieModel.temp_ban_until < now),
                    CookieModel.is_permanently_banned == False
                )
            
            return list(session.exec(statement).all())

    def get_pool_status_counts(self) -> Dict[str, int]:
        """获取Cookie池各项统计数据"""
        now = datetime.now()
        with session_scope() as session:
            # 总账号数
            total = session.exec(select(func.count(func.distinct(CookieModel.account_id)))).one()
            
            # 可用账号数
            available = session.exec(select(func.count(func.distinct(CookieModel.account_id))).where(
                CookieModel.is_available == True,
                or_(CookieModel.expire_time == None, CookieModel.expire_time > now),
                or_(CookieModel.temp_ban_until == None, CookieModel.temp_ban_until < now),
                CookieModel.is_permanently_banned == False
            )).one()
            
            # 临时封禁
            temp_banned = session.exec(select(func.count(func.distinct(CookieModel.account_id))).where(
                CookieModel.temp_ban_until != None,
                CookieModel.temp_ban_until > now,
                CookieModel.is_permanently_banned == False
            )).one()
            
            # 永久封禁
            perm_banned = session.exec(select(func.count(func.distinct(CookieModel.account_id))).where(
                CookieModel.is_permanently_banned == True
            )).one()
            
            # 过期账号 (added for completeness with schema)
            expired = session.exec(select(func.count(func.distinct(CookieModel.account_id))).where(
                 CookieModel.expire_time != None, 
                 CookieModel.expire_time < now
            )).one()

            return {
                "total": total,
                "available": available,
                "temp_banned": temp_banned,
                "perm_banned": perm_banned,
                "expired": expired
            }

    def get_banned_accounts_details(self) -> Tuple[List[Dict], List[str]]:
        """获取被封禁账号详情 (临时, 永久)"""
        now = datetime.now()
        with session_scope() as session:
            # 临时封禁
            temp_stmt = select(CookieModel.account_id, func.max(CookieModel.temp_ban_until)).where(
                CookieModel.temp_ban_until != None,
                CookieModel.temp_ban_until > now,
                CookieModel.is_permanently_banned == False
            ).group_by(CookieModel.account_id)
            
            temp_results = session.exec(temp_stmt).all()
            
            temp_banned_details = []
            for acc_id, ban_until in temp_results:
                temp_banned_details.append({
                    "account_id": acc_id,
                    "temp_ban_until": ban_until
                })
            
            # 永久封禁
            perm_stmt = select(CookieModel.account_id).distinct().where(
                CookieModel.is_permanently_banned == True
            )
            perm_results = list(session.exec(perm_stmt).all())
            
            return temp_banned_details, perm_results

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
            
    def get_cookie_by_id(self, cookie_id: int) -> Optional[CookieModel]:
        """根据ID获取Cookie"""
        with session_scope() as session:
            return session.get(CookieModel, cookie_id)


# 全局单例
cookie_repo = CookieRepository()
