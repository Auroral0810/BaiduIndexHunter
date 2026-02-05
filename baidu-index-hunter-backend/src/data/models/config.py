"""
系统配置数据模型
"""
from datetime import datetime
from typing import Optional
from sqlmodel import Field
from src.data.models.base import BaseDataModel

class SystemConfigModel(BaseDataModel, table=True):
    """
    对应数据库中的 system_config 表
    """
    __tablename__ = "system_config"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    config_key: str = Field(..., max_length=50)
    config_value: Optional[str] = None
    description: Optional[str] = None
    update_time: Optional[datetime] = None
