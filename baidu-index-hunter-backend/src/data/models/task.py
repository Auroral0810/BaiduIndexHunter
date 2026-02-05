"""
爬虫任务数据模型
"""
import json
from datetime import datetime
from typing import Optional, Any, Dict, List
from sqlmodel import Field
from pydantic import field_validator
from src.data.models.base import BaseDataModel

class SpiderTaskModel(BaseDataModel, table=True):
    """
    对应数据库中的 spider_tasks 表
    """
    __tablename__ = "spider_tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(..., max_length=32)
    task_name: Optional[str] = None
    task_type: str = Field(..., description="任务类型")
    status: str = Field("pending", description="任务状态")
    parameters: Optional[str] = Field(None, description="任务参数(JSON字符串)")
    progress: float = Field(0.0)
    total_items: int = Field(0)
    completed_items: int = Field(0)
    failed_items: int = Field(0)
    create_time: datetime = Field(default_factory=datetime.now)
    start_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    checkpoint_path: Optional[str] = Field(None, description="检查点数据(JSON字符串)")
    output_files: Optional[str] = Field(None, description="输出文件路径(JSON字符串)")
    created_by: Optional[str] = None
    priority: int = Field(5)

    @property
    def parameters_dict(self) -> Dict:
        """获取参数字典 (从JSON字符串解析)"""
        if not self.parameters:
            return {}
        try:
            return json.loads(self.parameters)
        except:
            return {}

    @parameters_dict.setter
    def parameters_dict(self, value: Dict):
        """设置参数字典 (自动转JSON字符串)"""
        if value is None:
            self.parameters = None
        else:
            self.parameters = json.dumps(value, ensure_ascii=False)

    @field_validator('parameters', 'checkpoint_path', 'output_files', mode='before')
    @classmethod
    def parse_json_fields_on_init(cls, v):
        """
        兼容 Pydantic 初始化时的自动转换:
        如果传入的是 dict/list，自动转成 json 字符串存入数据库字段
        """
        if isinstance(v, (dict, list)):
            return json.dumps(v, ensure_ascii=False)
        return v

class TaskQueueModel(BaseDataModel, table=True):
    """
    对应数据库中的 task_queue 表
    """
    __tablename__ = "task_queue"

    id: Optional[int] = Field(default=None, primary_key=True)
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
