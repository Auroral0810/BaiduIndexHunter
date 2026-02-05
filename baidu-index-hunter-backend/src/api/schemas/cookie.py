"""
Cookie 管理 Schema 模块
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class CookieStatus(str, Enum):
    """Cookie 状态枚举"""
    AVAILABLE = "available"
    TEMP_BANNED = "temp_banned"
    PERM_BANNED = "perm_banned"
    EXPIRED = "expired"


# ============== 请求 Schema ==============

class ListCookiesRequest(BaseModel):
    """获取 Cookie 列表请求"""
    account_id: Optional[str] = Field(None, description="账号ID过滤")
    status: Optional[CookieStatus] = Field(None, description="状态过滤")
    available_only: bool = Field(False, description="仅返回可用Cookie")
    page: int = Field(1, ge=1, description="页码")
    limit: int = Field(10, ge=1, le=100, description="每页条数")


class AddCookieRequest(BaseModel):
    """添加 Cookie 请求"""
    account_id: str = Field(..., description="账号ID")
    cookie_data: Any = Field(..., description="Cookie数据（字典、JSON字符串或cookie字符串）")
    expire_days: Optional[int] = Field(365, description="过期天数")


class UpdateCookieRequest(BaseModel):
    """更新 Cookie 请求"""
    cookies: Optional[Dict[str, str]] = Field(None, description="Cookie键值对")
    expire_days: Optional[int] = Field(None, description="过期天数")


class BanAccountRequest(BaseModel):
    """临时封禁账号请求"""
    ban_hours: int = Field(24, ge=1, description="封禁时长(小时)")


class UpdateAccountIdRequest(BaseModel):
    """更新账号ID请求"""
    new_account_id: str = Field(..., description="新账号ID")


# ============== 响应 Schema ==============

class CookieItemResponse(BaseModel):
    """Cookie 列表项"""
    account_id: str = Field(..., description="账号ID")
    cookies: Dict[str, str] = Field({}, description="Cookie键值对")
    expire_time: Optional[datetime] = Field(None, description="过期时间")
    is_available: bool = Field(True, description="是否可用")
    is_permanently_banned: bool = Field(False, description="是否永久封禁")
    temp_ban_until: Optional[datetime] = Field(None, description="临时封禁到期时间")


class CookieListResponse(BaseModel):
    """Cookie 列表响应数据"""
    items: List[CookieItemResponse] = Field([], description="Cookie列表")
    total: int = Field(0, description="总数量")


class CookiePoolStatusResponse(BaseModel):
    """Cookie 池状态响应"""
    total_accounts: int = Field(0, description="总账号数")
    available_accounts: int = Field(0, description="可用账号数")
    temp_banned_accounts: int = Field(0, description="临时封禁账号数")
    perm_banned_accounts: int = Field(0, description="永久封禁账号数")
    expired_accounts: int = Field(0, description="过期账号数")


class CookieUsageResponse(BaseModel):
    """Cookie 使用量响应"""
    account_id: str = Field(..., description="账号ID")
    usage_date: str = Field(..., description="日期")
    usage_count: int = Field(0, description="使用次数")


class TodayCookieUsageResponse(BaseModel):
    """今日 Cookie 使用量汇总响应"""
    date: str = Field(..., description="日期")
    total_usage: int = Field(0, description="总使用次数")
    account_count: int = Field(0, description="使用账号数")
    details: List[CookieUsageResponse] = Field([], description="详情列表")


class SyncResultResponse(BaseModel):
    """同步操作结果响应"""
    success: bool = Field(..., description="是否成功")
    count: int = Field(0, description="同步数量")
    message: str = Field("", description="结果消息")


class SingleCookieTestResult(BaseModel):
    """单账号测试结果项"""
    account_id: str = Field(..., description="测试的账号ID")
    status: int = Field(..., description="测试状态码")
    message: str = Field(..., description="测试结果消息")
    is_valid: bool = Field(..., description="是否有效")
    action_taken: str = Field(..., description="执行的操作")


class TestResultResponse(BaseModel):
    """测试结果响应 (批量)"""
    valid_accounts: List[str] = Field([], description="可用的账号ID列表")
    banned_accounts: List[str] = Field([], description="被封禁的账号ID列表")
    not_login_accounts: List[str] = Field([], description="未登录的账号ID列表")
    total_tested: int = Field(0, description="测试的总账号数")
    valid_count: int = Field(0, description="可用的账号数")
    banned_count: int = Field(0, description="被封禁的账号数")
    not_login_count: int = Field(0, description="未登录的账号数")


class BannedAccountResponse(BaseModel):
    """被封禁账号响应"""
    account_id: str = Field(..., description="账号ID")
    ban_type: str = Field(..., description="封禁类型")
    ban_until: Optional[datetime] = Field(None, description="封禁到期时间")

