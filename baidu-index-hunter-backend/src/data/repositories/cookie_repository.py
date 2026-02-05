"""
Cookie 仓储类
处理具体的 Cookie 数据库操作
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlmodel import select, func, col, or_, and_
from src.data.database import session_scope
from src.data.repositories.base_repository import BaseRepository
from src.data.models.cookie import CookieModel

class CookieRepository(BaseRepository[CookieModel]):
    def __init__(self):
        super().__init__(CookieModel)

    def get_by_account_id(self, account_id: str) -> List[CookieModel]:
        """获取指定账号的所有 Cookie"""
        with session_scope() as session:
            statement = select(CookieModel).where(CookieModel.account_id == account_id)
            return session.exec(statement).all()

    def delete_by_account_id(self, account_id: str) -> int:
        """删除指定账号的所有 Cookie"""
        with session_scope() as session:
            statement = select(CookieModel).where(CookieModel.account_id == account_id)
            cookies = session.exec(statement).all()
            count = len(cookies)
            for cookie in cookies:
                session.delete(cookie)
            session.commit()
            return count

    def get_unique_account_ids(self) -> List[str]:
        """获取所有唯一的账号ID"""
        with session_scope() as session:
            statement = select(CookieModel.account_id).distinct()
            return session.exec(statement).all()

    def get_available_account_ids(self) -> List[str]:
        """获取所有可用的唯一账号ID"""
        now = datetime.now()
        with session_scope() as session:
            # 条件: is_available=True 且 not expired 且 not temp_banned 且 not perm_banned
            statement = select(CookieModel.account_id).distinct().where(
                CookieModel.is_available == True,
                or_(CookieModel.expire_time == None, CookieModel.expire_time > now),
                or_(CookieModel.temp_ban_until == None, CookieModel.temp_ban_until < now),
                CookieModel.is_permanently_banned == False
            )
            return session.exec(statement).all()

    def count_by_status(self) -> Dict[str, int]:
        """获取各类状态的账号计数 (Total, Available, TempBanned, PermBanned)"""
        now = datetime.now()
        with session_scope() as session:
            # Total
            total_stmt = select(func.count(func.distinct(CookieModel.account_id)))
            total = session.exec(total_stmt).one()

            # Perm Banned
            perm_stmt = select(func.count(func.distinct(CookieModel.account_id))).where(
                CookieModel.is_permanently_banned == True
            )
            perm_banned = session.exec(perm_stmt).one()

            # Temp Banned (且非永久封禁)
            temp_stmt = select(func.count(func.distinct(CookieModel.account_id))).where(
                CookieModel.temp_ban_until != None,
                CookieModel.temp_ban_until > now,
                CookieModel.is_permanently_banned == False
            )
            temp_banned = session.exec(temp_stmt).one()

            # Available
            avail_stmt = select(func.count(func.distinct(CookieModel.account_id))).where(
                CookieModel.is_available == True,
                or_(CookieModel.expire_time == None, CookieModel.expire_time > now),
                or_(CookieModel.temp_ban_until == None, CookieModel.temp_ban_until < now),
                CookieModel.is_permanently_banned == False
            )
            available = session.exec(avail_stmt).one()

            return {
                "total": total,
                "perm_banned": perm_banned,
                "temp_banned": temp_banned,
                "available": available
            }

    def get_paginated_cookies(self, page: int, page_size: int, 
                              account_id: Optional[str] = None,
                              status_filter: Optional[str] = None,
                              is_available: Optional[bool] = None) -> Tuple[List[CookieModel], int]:
        """分页查询 Cookie"""
        now = datetime.now()
        offset = (page - 1) * page_size
        
        with session_scope() as session:
            query = select(CookieModel)
            
            # 过滤条件
            if account_id:
                query = query.where(col(CookieModel.account_id).contains(account_id))
            
            if is_available is not None:
                query = query.where(CookieModel.is_available == is_available)
                
            if status_filter:
                if status_filter == 'temp_banned':
                    query = query.where(
                        CookieModel.temp_ban_until != None,
                        CookieModel.temp_ban_until > now,
                        CookieModel.is_permanently_banned == False
                    )
                elif status_filter == 'perm_banned':
                    query = query.where(CookieModel.is_permanently_banned == True)
                elif status_filter == 'expired':
                    query = query.where(CookieModel.expire_time != None, CookieModel.expire_time < now)
                elif status_filter == 'normal':
                    query = query.where(
                        CookieModel.is_available == True,
                        or_(CookieModel.expire_time == None, CookieModel.expire_time > now),
                        or_(CookieModel.temp_ban_until == None, CookieModel.temp_ban_until < now)
                    )

            # 获取总数 (Count)
            # 为了性能，这里简单的 count 方式可能需要优化，但对于简单分页足够
            count_query = select(func.count()).select_from(query.subquery())
            total = session.exec(count_query).one()

            # 排序和分页
            query = query.order_by(col(CookieModel.id).desc()).offset(offset).limit(page_size)
            results = session.exec(query).all()
            
            return results, total

    def update_status_batch(self, account_id: str, updates: Dict[str, Any]) -> int:
        """批量更新某账号所有 Cookie 的状态"""
        with session_scope() as session:
            statement = select(CookieModel).where(CookieModel.account_id == account_id)
            cookies = session.exec(statement).all()
            count = 0
            for cookie in cookies:
                for k, v in updates.items():
                    setattr(cookie, k, v)
                session.add(cookie)
                count += 1
            session.commit()
            return count

# 全局单例
cookie_repo = CookieRepository()
