"""
系统配置 Schema 模块
"""
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, RootModel


# ============== 请求 Schema ==============

class ListConfigsRequest(BaseModel):
    """获取配置列表请求"""
    prefix: Optional[str] = Field(None, description="配置键前缀过滤")


class SetConfigRequest(BaseModel):
    """设置配置项请求"""
    key: str = Field(..., min_length=1, max_length=50, description="配置键")
    value: Any = Field(..., description="配置值")
    description: Optional[str] = Field(None, description="配置描述")


class BatchSetConfigRequest(RootModel):
    """批量设置配置项请求（字典形式: {key: value}）"""
    root: Dict[str, Any]


# ============== 响应 Schema ==============

class ConfigItemResponse(BaseModel):
    """配置项响应"""
    key: str = Field(..., description="配置键")
    value: Any = Field(None, description="配置值")
    description: Optional[str] = Field(None, description="配置描述")
    update_time: Optional[datetime] = Field(None, description="更新时间")


class ConfigListResponse(BaseModel):
    """配置列表响应"""
    configs: Dict[str, Any] = Field({}, description="配置项字典")
