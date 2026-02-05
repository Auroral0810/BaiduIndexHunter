"""
API Schemas 统一导出
"""
# 基础模块
from src.api.schemas.base import (
    BaseResponse,
    PaginatedData,
    PaginationParams,
    ErrorDetail
)

# 任务管理
from src.api.schemas.task import (
    TaskType,
    TaskStatus,
    CreateTaskRequest,
    SearchIndexParams,
    RegionDistributionParams,
    ListTasksRequest,
    TaskCreateResponse,
    TaskItemResponse,
    TaskListResponse,
    TaskDetailResponse
)

# Cookie 管理
from src.api.schemas.cookie import (
    CookieStatus,
    ListCookiesRequest,
    AddCookieRequest,
    UpdateCookieRequest,
    BanAccountRequest,
    CookieItemResponse,
    CookieListResponse,
    CookiePoolStatusResponse,
    CookieUsageResponse,
    TodayCookieUsageResponse
)

# 区域数据
from src.api.schemas.region import (
    RegionItemResponse,
    ProvinceItemResponse,
    CityItemResponse,
    RegionPathResponse,
    RegionChildrenResponse,
    AllProvincesResponse,
    AllCitiesResponse,
    ProvinceCitiesResponse
)

# 统计数据
from src.api.schemas.statistics import (
    GetSpiderStatisticsRequest,
    GetKeywordStatisticsRequest,
    TaskSummaryResponse,
    SpiderStatisticsItemResponse,
    SpiderStatisticsResponse,
    KeywordStatisticsItemResponse,
    KeywordStatisticsResponse,
    DashboardDataResponse
)

# 配置管理
from src.api.schemas.config import (
    SetConfigRequest,
    BatchSetConfigRequest,
    ConfigItemResponse,
    ConfigListResponse
)

# 关键词检查
from src.api.schemas.word_check import (
    CheckWordsRequest,
    CheckSingleWordRequest,
    WordCheckResultItem,
    CheckWordsResponse,
    CheckSingleWordResponse
)

__all__ = [
    # 基础
    "BaseResponse", "PaginatedData", "PaginationParams", "ErrorDetail",
    # 任务
    "TaskType", "TaskStatus", "CreateTaskRequest", "SearchIndexParams",
    "RegionDistributionParams", "ListTasksRequest", "TaskCreateResponse",
    "TaskItemResponse", "TaskListResponse", "TaskDetailResponse",
    # Cookie
    "CookieStatus", "ListCookiesRequest", "AddCookieRequest", 
    "UpdateCookieRequest", "BanAccountRequest", "CookieItemResponse",
    "CookieListResponse", "CookiePoolStatusResponse", "CookieUsageResponse",
    "TodayCookieUsageResponse",
    # 区域
    "RegionItemResponse", "ProvinceItemResponse", "CityItemResponse",
    "RegionPathResponse", "RegionChildrenResponse", "AllProvincesResponse",
    "AllCitiesResponse", "ProvinceCitiesResponse",
    # 统计
    "GetSpiderStatisticsRequest", "GetKeywordStatisticsRequest",
    "TaskSummaryResponse", "SpiderStatisticsItemResponse",
    "SpiderStatisticsResponse", "KeywordStatisticsItemResponse",
    "KeywordStatisticsResponse", "DashboardDataResponse",
    # 配置
    "SetConfigRequest", "BatchSetConfigRequest", "ConfigItemResponse",
    "ConfigListResponse",
    # 关键词检查
    "CheckWordsRequest", "CheckSingleWordRequest", "WordCheckResultItem",
    "CheckWordsResponse", "CheckSingleWordResponse"
]
