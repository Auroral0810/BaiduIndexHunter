"""
统计数据 Schema 模块
"""
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============== 请求 Schema ==============

class GetSpiderStatisticsRequest(BaseModel):
    """获取爬虫统计请求"""
    start_date: Optional[str] = Field(None, description="开始日期 YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="结束日期 YYYY-MM-DD")
    task_type: Optional[str] = Field(None, description="任务类型过滤")


class GetKeywordStatisticsRequest(BaseModel):
    """获取关键词统计请求"""
    task_id: Optional[str] = Field(None, description="任务ID过滤")
    limit: int = Field(20, ge=1, le=100, description="返回数量")


# ============== 响应 Schema ==============

class TaskSummaryResponse(BaseModel):
    """任务摘要响应"""
    total_tasks: int = Field(0, description="总任务数")
    pending_tasks: int = Field(0, description="待处理任务数")
    running_tasks: int = Field(0, description="运行中任务数")
    completed_tasks: int = Field(0, description="已完成任务数")
    failed_tasks: int = Field(0, description="失败任务数")
    total_crawled_items: int = Field(0, description="累计爬取数据条数")
    today_crawled_items: int = Field(0, description="今日爬取数据条数")


class SpiderStatisticsItemResponse(BaseModel):
    """爬虫统计项"""
    stat_date: str = Field(..., description="统计日期")
    task_type: str = Field(..., description="任务类型")
    total_tasks: int = Field(0)
    completed_tasks: int = Field(0)
    failed_tasks: int = Field(0)
    total_items: int = Field(0)
    success_rate: float = Field(0.0)
    avg_duration: float = Field(0.0)
    cookie_usage: int = Field(0)
    cookie_ban_count: int = Field(0)


class SpiderStatisticsResponse(BaseModel):
    """爬虫统计响应"""
    statistics: List[SpiderStatisticsItemResponse] = Field([])
    total: int = Field(0)


class KeywordStatisticsItemResponse(BaseModel):
    """关键词统计项"""
    keyword: str = Field(..., description="关键词")
    item_count: int = Field(0, description="数据条数")
    avg_value: Optional[float] = Field(None, description="平均值")
    max_value: Optional[float] = Field(None, description="最大值")
    min_value: Optional[float] = Field(None, description="最小值")


class KeywordStatisticsResponse(BaseModel):
    """关键词统计响应"""
    keywords: List[KeywordStatisticsItemResponse] = Field([])
    total: int = Field(0)


class DashboardDataResponse(BaseModel):
    """仪表盘数据响应"""
    task_summary: TaskSummaryResponse = Field(..., description="任务摘要")
    cookie_status: Dict[str, int] = Field({}, description="Cookie状态统计")
    recent_tasks: List[Dict[str, Any]] = Field([], description="最近任务")
    daily_statistics: List[Dict[str, Any]] = Field([], description="每日统计")
