"""
任务管理 Schema 模块
"""
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from enum import Enum


class TaskType(str, Enum):
    """任务类型枚举"""
    SEARCH_INDEX = "search_index"
    FEED_INDEX = "feed_index"
    WORD_GRAPH = "word_graph"
    DEMOGRAPHIC_ATTRIBUTES = "demographic_attributes"
    INTEREST_PROFILE = "interest_profile"
    REGION_DISTRIBUTION = "region_distribution"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


# ============== 请求 Schema ==============

class CreateTaskRequest(BaseModel):
    """创建任务请求"""
    taskType: TaskType = Field(..., description="任务类型")
    parameters: Dict[str, Any] = Field(..., description="任务参数")
    priority: int = Field(5, ge=1, le=10, description="优先级(1-10)")


class SearchIndexParams(BaseModel):
    """搜索指数任务参数"""
    keywords: List[str] = Field(..., min_length=1, description="关键词列表")
    cities: List[str] = Field(..., min_length=1, description="城市代码列表")
    days: Optional[int] = Field(None, description="天数")
    date_ranges: Optional[List[List[str]]] = Field(None, description="日期范围")
    year_range: Optional[List[int]] = Field(None, description="年份范围 [start, end]")
    kind: Optional[str] = Field(None, description="数据来源：PC/移动/PC+移动")
    resume: bool = Field(False, description="是否恢复任务")
    task_id: Optional[str] = Field(None, description="恢复任务时的原任务ID")


class RegionDistributionParams(BaseModel):
    """地域分布任务参数"""
    keywords: List[str] = Field(..., min_length=1, description="关键词列表")
    regions: List[str] = Field(..., min_length=1, description="区域代码列表")
    output_format: str = Field("csv", description="输出格式: csv/excel")
    region_level: Optional[str] = Field(None, description="区域级别")


class ListTasksRequest(BaseModel):
    """获取任务列表请求"""
    status: Optional[str] = Field(None, description="状态过滤")
    task_type: Optional[str] = Field(None, description="类型过滤")
    created_by: Optional[str] = Field(None, description="创建者过滤")
    keyword: Optional[str] = Field(None, description="关键词搜索")
    limit: int = Field(10, ge=1, le=100, description="每页数量")
    offset: int = Field(0, ge=0, description="偏移量")


class DownloadFileRequest(BaseModel):
    """下载文件请求"""
    task_id: str = Field(..., description="任务ID")
    file_type: str = Field("csv", description="文件类型")


# ============== 响应 Schema ==============

class TaskCreateResponse(BaseModel):
    """任务创建响应数据"""
    taskId: str = Field(..., description="任务ID")


class TaskItemResponse(BaseModel):
    """任务列表项"""
    task_id: str = Field(..., description="任务ID")
    task_name: Optional[str] = Field(None, description="任务名称")
    task_type: str = Field(..., description="任务类型")
    status: str = Field(..., description="任务状态")
    progress: float = Field(0.0, description="进度(0-100)")
    total_items: int = Field(0, description="总项目数")
    completed_items: int = Field(0, description="已完成项目数")
    failed_items: int = Field(0, description="失败项目数")
    create_time: Optional[datetime] = Field(None, description="创建时间")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    priority: int = Field(5, description="优先级")


class TaskListResponse(BaseModel):
    """任务列表响应数据"""
    tasks: List[TaskItemResponse] = Field([], description="任务列表")
    total: int = Field(0, description="总数量")


class TaskDetailResponse(TaskItemResponse):
    """任务详情响应数据（扩展基础信息）"""
    parameters: Optional[Dict[str, Any]] = Field(None, description="任务参数")
    error_message: Optional[str] = Field(None, description="错误信息")
    checkpoint_path: Optional[Any] = Field(None, description="检查点数据")
    output_files: Optional[Any] = Field(None, description="输出文件")
    logs: Optional[List[Dict[str, Any]]] = Field(None, description="任务日志")

