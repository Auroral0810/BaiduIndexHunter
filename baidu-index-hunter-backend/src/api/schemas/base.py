"""
基础 Schema 模块
定义统一的请求/响应格式及分页参数
"""
from typing import Any, Generic, TypeVar, Optional, List
from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """
    统一响应格式
    所有 API 返回均遵循此结构
    """
    code: int = Field(10000, description="状态码")
    msg: str = Field("请求成功", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")


class PaginatedData(BaseModel, Generic[T]):
    """
    分页数据结构
    """
    items: List[T] = Field([], description="数据列表")
    total: int = Field(0, description="总记录数")
    page: int = Field(1, description="当前页码")
    limit: int = Field(10, description="每页条数")


class PaginationParams(BaseModel):
    """
    分页请求参数
    """
    page: int = Field(1, ge=1, description="页码，从1开始")
    limit: int = Field(10, ge=1, le=100, description="每页条数")
    offset: Optional[int] = Field(None, ge=0, description="偏移量（可选）")


class ErrorDetail(BaseModel):
    """
    错误详情
    """
    field: Optional[str] = Field(None, description="出错字段")
    message: str = Field(..., description="错误描述")
