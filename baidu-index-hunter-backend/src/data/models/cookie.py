"""
Cookie 数据模型
"""
from datetime import datetime
from typing import Optional
from sqlmodel import Field
from src.data.models.base import BaseDataModel

class CookieModel(BaseDataModel, table=True):
    """
    对应数据库中的 cookies 表
    """
    __tablename__ = "cookies"
    
    id: Optional[int] = Field(default=None, primary_key=True, description="自增ID")
    account_id: str = Field(..., description="账号ID")
    cookie_name: str = Field(..., description="Cookie名称")
    cookie_value: str = Field(..., description="Cookie明文值")
    last_updated: Optional[datetime] = Field(None, description="最后更新时间")
    expire_time: Optional[datetime] = Field(None, description="过期时间")
    is_available: bool = Field(True, description="是否可用")
    is_permanently_banned: bool = Field(False, description="是否永久封禁")
    temp_ban_until: Optional[datetime] = Field(None, description="临时封禁到期时间")

    @classmethod
    def from_db_row(cls, row: dict):
        if not row:
            return None
        # 处理 MySQL 中 tinyint(1) 转 bool 的逻辑
        if 'is_available' in row:
            row['is_available'] = bool(row['is_available'])
        if 'is_permanently_banned' in row:
            row['is_permanently_banned'] = bool(row['is_permanently_banned'])
        return super().from_db_row(row)

class CookieDailyUsageModel(BaseDataModel, table=True):
    """
    对应数据库中的 cookie_daily_usage 表
    """
    __tablename__ = "cookie_daily_usage"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: str = Field(...)
    usage_date: datetime = Field(...)
    usage_count: int = Field(0)
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
