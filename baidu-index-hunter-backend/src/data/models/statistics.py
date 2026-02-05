"""
爬虫统计与汇总数据模型
"""
import json
from datetime import date, datetime
from typing import Optional, Any, Dict
from src.data.models.base import BaseDataModel
from pydantic import Field, field_validator

class SpiderStatisticsModel(BaseDataModel):
    """
    对应数据库中的 spider_statistics 表
    """
    id: Optional[int] = Field(None)
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

class TaskStatisticsModel(BaseDataModel):
    """
    对应数据库中的 task_statistics 表
    """
    id: Optional[int] = Field(None)
    task_id: str = Field(..., max_length=32)
    keyword: Optional[str] = None
    city_code: Optional[str] = None
    date_range: Optional[str] = None
    data_type: Optional[str] = None
    item_count: int = Field(0)
    avg_value: Optional[float] = None
    max_value: Optional[float] = None
    min_value: Optional[float] = None
    sum_value: Optional[float] = None
    extra_data: Any = Field(None, description="额外数据(JSON)")
    create_time: Optional[datetime] = None

    @field_validator('extra_data', mode='before')
    @classmethod
    def parse_extra_data(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return v
        return v

    def to_db_dict(self, exclude_fields: set = None) -> Dict[str, Any]:
        data = super().to_db_dict(exclude_fields)
        if 'extra_data' in data and not isinstance(data['extra_data'], (str, type(None))):
            data['extra_data'] = json.dumps(data['extra_data'], ensure_ascii=False)
        return data
