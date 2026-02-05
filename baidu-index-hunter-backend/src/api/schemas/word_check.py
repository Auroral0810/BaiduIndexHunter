"""
关键词检查 Schema 模块
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


# ============== 请求 Schema ==============

class CheckWordsRequest(BaseModel):
    """批量检查关键词请求"""
    words: List[str] = Field(..., min_length=1, description="关键词列表")


class CheckSingleWordRequest(BaseModel):
    """检查单个关键词请求"""
    word: str = Field(..., min_length=1, description="关键词")


# ============== 响应 Schema ==============

class WordCheckResultItem(BaseModel):
    """单个关键词检查结果"""
    exists: bool = Field(..., description="是否存在")
    error: Optional[str] = Field(None, description="错误信息")


class CheckWordsResponse(BaseModel):
    """批量检查关键词响应"""
    results: Dict[str, WordCheckResultItem] = Field({}, description="检查结果字典")


class CheckSingleWordResponse(BaseModel):
    """单个关键词检查响应"""
    word: str = Field(..., description="关键词")
    exists: bool = Field(..., description="是否存在")
    error: Optional[str] = Field(None, description="错误信息")
