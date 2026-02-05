"""
任务日志数据模型
"""
import json
from datetime import datetime
from typing import Optional, Any, Dict
from sqlmodel import Field
from pydantic import field_validator
from src.data.models.base import BaseDataModel

class TaskLogModel(BaseDataModel, table=True):
    """
    对应数据库中的 task_logs 表
    """
    __tablename__ = "task_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(..., max_length=32)
    log_level: str = Field(..., description="日志级别(info/warning/error/debug)")
    message: str = Field(...)
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Optional[str] = Field(None, description="详细信息(JSON字符串)")

    @field_validator('details', mode='before')
    @classmethod
    def parse_details_on_init(cls, v):
        """兼容 Pydantic 初始化: dict -> json str"""
        if isinstance(v, (dict, list)):
            return json.dumps(v, ensure_ascii=False)
        return v
    
    @property
    def details_dict(self) -> Dict:
        """获取详细信息字典"""
        if not self.details:
            return {}
        try:
            return json.loads(self.details)
        except:
            return {}
    
    @details_dict.setter
    def details_dict(self, value: Dict):
        """设置详细信息字典"""
        if value is None:
            self.details = None
        else:
            self.details = json.dumps(value, ensure_ascii=False)
