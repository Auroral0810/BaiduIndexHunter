"""
爬虫统计与汇总数据模型
"""
import json
from datetime import date, datetime
from typing import Optional, Any, Dict
from sqlmodel import Field
from pydantic import field_validator
from src.data.models.base import BaseDataModel

class SpiderStatisticsModel(BaseDataModel, table=True):
    """
    对应数据库中的 spider_statistics 表
    """
    __tablename__ = "spider_statistics"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    stat_date: date = Field(...)
    task_type: str = Field(...)
    total_tasks: int = Field(0)
    completed_tasks: int = Field(0)
    failed_tasks: int = Field(0)
    total_items: int = Field(0)
    total_crawled_items: int = Field(0)
    success_rate: float = Field(0.0)
    avg_duration: float = Field(0.0)
    cookie_usage: int = Field(0)
    cookie_ban_count: int = Field(0)
    update_time: Optional[datetime] = None

class TaskStatisticsModel(BaseDataModel, table=True):
    """
    对应数据库中的 task_statistics 表
    """
    __tablename__ = "task_statistics"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(..., max_length=32)
    keyword: Optional[str] = None
    city_code: Optional[str] = None
    city_name: Optional[str] = None
    date_range: Optional[str] = None
    data_type: Optional[str] = None
    item_count: int = Field(0)
    success_count: int = Field(0)
    fail_count: int = Field(0)
    avg_value: Optional[float] = None
    max_value: Optional[float] = None
    min_value: Optional[float] = None
    sum_value: Optional[float] = None
    extra_data: Optional[str] = Field(None, description="额外数据(JSON字符串)")
    create_time: Optional[datetime] = None

    @field_validator('extra_data', mode='before')
    @classmethod
    def parse_extra_data_on_init(cls, v):
        """兼容 Pydantic 初始化: dict -> json str"""
        if isinstance(v, (dict, list)):
            return json.dumps(v, ensure_ascii=False)
        return v
    
    @property
    def extra_data_dict(self) -> Dict:
        """获取额外数据字典"""
        if not self.extra_data:
            return {}
        try:
            return json.loads(self.extra_data)
        except:
            return {}
    
    @extra_data_dict.setter
    def extra_data_dict(self, value: Dict):
        """设置额外数据字典"""
        if value is None:
            self.extra_data = None
        else:
            self.extra_data = json.dumps(value, ensure_ascii=False)
