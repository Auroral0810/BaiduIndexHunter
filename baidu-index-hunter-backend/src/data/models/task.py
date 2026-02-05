"""
爬虫任务数据模型
"""
import json
from datetime import datetime
from typing import Optional, Any, Dict, List
from src.data.models.base import BaseDataModel
from pydantic import Field, field_validator

class SpiderTaskModel(BaseDataModel):
    """
    对应数据库中的 spider_tasks 表
    """
    id: Optional[int] = Field(None)
    task_id: str = Field(..., max_length=32)
    task_name: Optional[str] = None
    task_type: str = Field(..., description="任务类型")
    status: str = Field("pending", description="任务状态")
    parameters: Any = Field(None, description="任务参数(JSON)")
    progress: float = Field(0.0)
    total_items: int = Field(0)
    completed_items: int = Field(0)
    failed_items: int = Field(0)
    create_time: datetime = Field(default_factory=datetime.now)
    start_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    checkpoint_path: Optional[Any] = Field(None, description="检查点数据(JSON)")
    output_files: Optional[Any] = Field(None, description="输出文件路径(JSON)")
    created_by: Optional[str] = None
    priority: int = Field(5)

    @field_validator('parameters', 'checkpoint_path', 'output_files', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        """自动尝试将字符串形式的 JSON 转换为字典/列表"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return v
        return v

    def to_db_dict(self, exclude_fields: set = None) -> Dict[str, Any]:
        """重写以确保 JSON 字段在入库前序列化为字符串"""
        data = super().to_db_dict(exclude_fields)
        for field in ['parameters', 'checkpoint_path', 'output_files']:
            if field in data and not isinstance(data[field], (str, type(None))):
                data[field] = json.dumps(data[field], ensure_ascii=False)
        return data

class TaskQueueModel(BaseDataModel):
    """
    对应数据库中的 task_queue 表
    """
    id: Optional[int] = Field(None)
    task_id: str = Field(..., max_length=32)
    priority: int = Field(0)
    status: str = Field("waiting")
    worker_id: Optional[str] = None
    enqueue_time: datetime = Field(default_factory=datetime.now)
    start_time: Optional[datetime] = None
    complete_time: Optional[datetime] = None
    retry_count: int = Field(0)
    max_retries: int = Field(3)
    next_retry_time: Optional[datetime] = None
