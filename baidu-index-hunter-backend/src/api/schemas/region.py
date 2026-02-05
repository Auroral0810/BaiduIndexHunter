"""
区域数据 Schema 模块
"""
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field


# ============== 请求 Schema ==============

class GetCityByNameRequest(BaseModel):
    """根据城市名称获取城市代码请求"""
    name: str = Field(..., min_length=1, description="城市名称")


class GetProvinceByNameRequest(BaseModel):
    """根据省份名称获取省份代码请求"""
    name: str = Field(..., min_length=1, description="省份名称")


class GetRegionByNameRequest(BaseModel):
    """根据区域名称获取区域代码请求"""
    name: str = Field(..., min_length=1, description="区域名称")
    level: Optional[int] = Field(None, description="层级过滤")


class UpdateCityProvinceRequest(BaseModel):
    """更新城市省份归属请求"""
    city_code: str = Field(..., description="城市代码")
    province_code: str = Field(..., description="省份代码")


class BatchUpdateCityProvinceRequest(BaseModel):
    """批量更新城市省份归属请求"""
    mappings: List[Dict[str, str]] = Field(..., description="城市-省份映射列表")


# ============== 响应 Schema ==============

class RegionItemResponse(BaseModel):
    """区域信息"""
    region_code: str = Field(..., description="区域代码")
    region_name: str = Field(..., description="区域名称")
    layer_level: int = Field(..., description="层级：1-省级，2-地级市...")
    parent_code: Optional[str] = Field(None, description="父级区域代码")


class ProvinceItemResponse(BaseModel):
    """省份信息"""
    province_code: str = Field(..., description="省份代码")
    province_name: str = Field(..., description="省份名称")
    region_name: Optional[str] = Field(None, description="所属大区")


class CityItemResponse(BaseModel):
    """城市信息"""
    city_code: str = Field(..., description="城市代码")
    city_name: str = Field(..., description="城市名称")
    province_code: Optional[str] = Field(None, description="所属省份代码")
    province_name: Optional[str] = Field(None, description="所属省份名称")


class RegionPathResponse(BaseModel):
    """区域路径响应"""
    path: List[RegionItemResponse] = Field([], description="从顶级到当前区域的完整路径")


class RegionChildrenResponse(BaseModel):
    """区域子级响应"""
    parent: RegionItemResponse = Field(..., description="父级区域")
    children: List[RegionItemResponse] = Field([], description="子级区域列表")


class AllProvincesResponse(BaseModel):
    """所有省份响应"""
    provinces: List[ProvinceItemResponse] = Field([], description="省份列表")
    total: int = Field(0, description="总数量")


class AllCitiesResponse(BaseModel):
    """所有城市响应"""
    cities: List[CityItemResponse] = Field([], description="城市列表")
    total: int = Field(0, description="总数量")


class ProvinceCitiesResponse(BaseModel):
    """省份下属城市响应"""
    province_code: str = Field(..., description="省份代码")
    province_name: str = Field(..., description="省份名称")
    cities: List[CityItemResponse] = Field([], description="城市列表")


class AllRegionsResponse(BaseModel):
    """所有区域关系响应"""
    regions: List[Any] = Field([], description="区域关系列表")
    total: int = Field(0, description="总数量")


class SyncResultResponse(BaseModel):
    """同步操作结果响应"""
    success: bool = Field(..., description="是否成功")
    count: int = Field(0, description="同步数量")
    message: str = Field("", description="结果消息")

