"""
系统配置 Schema 模块
"""
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field


# ============== 请求 Schema ==============

class SetConfigRequest(BaseModel):
    """设置配置项请求"""
    key: str = Field(..., min_length=1, max_length=50, description="配置键")
    value: Any = Field(..., description="配置值")
    description: Optional[str] = Field(None, description="配置描述")


class BatchSetConfigRequest(BaseModel):
    """批量设置配置项请求"""
    configs: List[SetConfigRequest] = Field(..., min_length=1, description="配置项列表")


# ============== 响应 Schema ==============

class ConfigItemResponse(BaseModel):
    """配置项响应"""
    key: str = Field(..., description="配置键")
    value: Any = Field(None, description="配置值")
    description: Optional[str] = Field(None, description="配置描述")
    update_time: Optional[datetime] = Field(None, description="更新时间")


class ConfigListResponse(BaseModel):
    """配置列表响应"""
    configs: List[ConfigItemResponse] = Field([], description="配置项列表")
    total: int = Field(0, description="总数量")
