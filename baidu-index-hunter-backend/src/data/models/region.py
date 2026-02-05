"""
区域地理数据模型
"""
from datetime import datetime
from typing import Optional
from src.data.models.base import BaseDataModel
from sqlmodel import Field

class RegionHierarchyModel(BaseDataModel, table=True):
    """区域层级模型 (region_hierarchy 表)"""
    __tablename__ = "region_hierarchy"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    region_code: str = Field(..., description="区域代码")
    region_name: str = Field(..., description="区域名称")
    layer_level: int = Field(..., description="层级：1-省级，2-地级市...")
    parent_code: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ProvinceModel(BaseDataModel, table=True):
    """省份模型 (province_region 表)"""
    __tablename__ = "province_region"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    province_code: str = Field(...)
    province_name: str = Field(...)
    region_name: Optional[str] = Field(None, description="所属大区（华东等）")

class CityModel(BaseDataModel, table=True):
    """地级市模型 (prefecture_city 表)"""
    __tablename__ = "prefecture_city"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    city_code: str = Field(...)
    city_name: str = Field(...)
    province_code: Optional[str] = None
    province_name: Optional[str] = None

class RegionChildrenModel(BaseDataModel, table=True):
    """
    对应数据库中的 region_children 表
    """
    __tablename__ = "region_children"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    parent_code: str = Field(...)
    child_code: str = Field(...)
    sort_order: int = Field(0)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
