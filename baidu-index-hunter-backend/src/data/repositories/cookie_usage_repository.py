"""
Cookie 使用量仓储类
处理 Cookie 每日使用量的数据库操作
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import date, datetime
from sqlmodel import select, col
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy import func

from src.data.database import session_scope
from src.data.repositories.base_repository import BaseRepository
from src.data.models.cookie import CookieDailyUsageModel

class CookieUsageRepository(BaseRepository[CookieDailyUsageModel]):
    def __init__(self):
        super().__init__(CookieDailyUsageModel)

    def get_usage_by_date(self, usage_date: date) -> List[CookieDailyUsageModel]:
        """获取指定日期的使用量数据"""
        with session_scope() as session:
            # sqlmodel 可能会将 date 转换为 datetime，这里确保类型匹配
            statement = select(CookieDailyUsageModel).where(
                func.date(CookieDailyUsageModel.usage_date) == usage_date
            )
            results = session.exec(statement).all()
            # 返回脱离 Session 的 Pydantic 对象，防止 DetachedInstanceError
            return [CookieDailyUsageModel.model_validate(r) for r in results]

    def update_usage(self, account_id: str, usage_date: date, count: int) -> None:
        """
        更新使用量 (UPSERT)
        """
        with session_scope() as session:
            insert_stmt = mysql_insert(CookieDailyUsageModel.__table__).values(
                account_id=account_id,
                usage_date=usage_date,
                usage_count=count
            )
            on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
                usage_count=insert_stmt.inserted.usage_count,
                update_time=func.now()
            )
            session.exec(on_duplicate_key_stmt)
            session.commit()

    def increment_usage(self, account_id: str, usage_date: date, increment: int = 1) -> None:
        """
        增加使用量 (UPSERT + increment)
        """
        with session_scope() as session:
            insert_stmt = mysql_insert(CookieDailyUsageModel.__table__).values(
                account_id=account_id,
                usage_date=usage_date,
                usage_count=increment
            )
            on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
                usage_count=CookieDailyUsageModel.__table__.c.usage_count + increment,
                update_time=func.now()
            )
            session.exec(on_duplicate_key_stmt)
            session.commit()

    def get_usage_stats(self, 
                        account_id: Optional[str] = None, 
                        start_date: Optional[date] = None, 
                        end_date: Optional[date] = None) -> List[CookieDailyUsageModel]:
        """获取使用量统计"""
        with session_scope() as session:
            query = select(CookieDailyUsageModel)
            
            if account_id:
                query = query.where(CookieDailyUsageModel.account_id == account_id)
            
            if start_date:
                query = query.where(func.date(CookieDailyUsageModel.usage_date) >= start_date)
            
            if end_date:
                query = query.where(func.date(CookieDailyUsageModel.usage_date) <= end_date)
            
            query = query.order_by(col(CookieDailyUsageModel.usage_date).desc(), col(CookieDailyUsageModel.usage_count).desc())
            
            results = session.exec(query).all()
            # 返回脱离 Session 的 Pydantic 对象
            return [CookieDailyUsageModel.model_validate(r) for r in results]

# 全局单例
cookie_usage_repo = CookieUsageRepository()
