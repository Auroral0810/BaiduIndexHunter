"""
系统配置数据模型
"""
from datetime import datetime
from typing import Optional
from src.data.models.base import BaseDataModel
from pydantic import Field

class SystemConfigModel(BaseDataModel):
    """
    对应数据库中的 system_config 表
    """
    id: Optional[int] = Field(None)
    config_key: str = Field(..., max_length=50)
    config_value: Optional[str] = None
    description: Optional[str] = None
    update_time: Optional[datetime] = None
