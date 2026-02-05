"""
任务日志数据模型
"""
import json
from datetime import datetime
from typing import Optional, Any, Dict
from src.data.models.base import BaseDataModel
from pydantic import Field, field_validator

class TaskLogModel(BaseDataModel):
    """
    对应数据库中的 task_logs 表
    """
    id: Optional[int] = Field(None)
    task_id: str = Field(..., max_length=32)
    log_level: str = Field(..., description="日志级别(info/warning/error/debug)")
    message: str = Field(...)
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Any = Field(None, description="详细信息(JSON)")

    @field_validator('details', mode='before')
    @classmethod
    def parse_details(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return v
        return v

    def to_db_dict(self, exclude_fields: set = None) -> Dict[str, Any]:
        data = super().to_db_dict(exclude_fields)
        if 'details' in data and not isinstance(data['details'], (str, type(None))):
            data['details'] = json.dumps(data['details'], ensure_ascii=False)
        return data
