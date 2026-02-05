"""
区域数据仓储类
处理 Region 相关的数据库操作
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlmodel import select, col
from sqlalchemy import func, update

from src.data.database import session_scope
from src.data.repositories.base_repository import BaseRepository
from src.data.models.region import RegionHierarchyModel, ProvinceModel, CityModel, RegionChildrenModel

class RegionRepository(BaseRepository[RegionHierarchyModel]):
    def __init__(self):
        super().__init__(RegionHierarchyModel)

    def get_all_provinces(self) -> List[ProvinceModel]:
        """获取所有省份数据"""
        with session_scope() as session:
            statement = select(ProvinceModel).order_by(ProvinceModel.province_code)
            results = session.exec(statement).all()
            return [ProvinceModel.model_validate(r) for r in results]

    def get_all_cities(self) -> List[CityModel]:
        """获取所有城市数据"""
        with session_scope() as session:
            statement = select(CityModel).order_by(CityModel.city_code)
            results = session.exec(statement).all()
            return [CityModel.model_validate(r) for r in results]

    def get_all_regions(self) -> List[RegionHierarchyModel]:
        """获取所有区域层级数据"""
        with session_scope() as session:
            statement = select(RegionHierarchyModel).order_by(RegionHierarchyModel.layer_level, RegionHierarchyModel.region_code)
            results = session.exec(statement).all()
            return [RegionHierarchyModel.model_validate(r) for r in results]

    def get_all_children_relations(self) -> List[RegionChildrenModel]:
        """获取所有区域父子关系"""
        with session_scope() as session:
            statement = select(RegionChildrenModel).order_by(RegionChildrenModel.parent_code, RegionChildrenModel.sort_order)
            results = session.exec(statement).all()
            return [RegionChildrenModel.model_validate(r) for r in results]
    
    def get_region_code_by_name(self, name: str, level: Optional[int] = None) -> Optional[str]:
        """根据名称获取区域代码"""
        with session_scope() as session:
            statement = select(RegionHierarchyModel.region_code).where(RegionHierarchyModel.region_name == name)
            if level is not None:
                statement = statement.where(RegionHierarchyModel.layer_level == level)
            
            result = session.exec(statement).first()
            return result
    
    def get_province_region_name(self, province_code: str) -> Optional[str]:
        """获取省份所属大区名称"""
        with session_scope() as session:
            statement = select(ProvinceModel.region_name).where(ProvinceModel.province_code == province_code)
            result = session.exec(statement).first()
            return result

    def get_provinces_by_region(self, region_name: str) -> List[Dict[str, Any]]:
        """获取指定大区的所有省份 (联合查询)"""
        with session_scope() as session:
            # Join ProvinceModel and RegionHierarchyModel to get level (though usually 1)
            # Simulating: 
            # SELECT pr.province_code, pr.province_name, COALESCE(rh.layer_level, 1) 
            # FROM province_region pr LEFT JOIN region_hierarchy rh ...
            
            statement = select(
                ProvinceModel.province_code, 
                ProvinceModel.province_name,
                RegionHierarchyModel.layer_level
            ).outerjoin(
                RegionHierarchyModel, ProvinceModel.province_code == RegionHierarchyModel.region_code
            ).where(
                ProvinceModel.region_name == region_name
            )
            
            results = session.exec(statement).all()
            normalized_results = []
            for r in results:
                normalized_results.append({
                    "code": r[0],
                    "name": r[1],
                    "level": r[2] if r[2] is not None else 1
                })
            return normalized_results

    def get_city_code_by_name(self, city_name: str) -> Optional[str]:
        """根据城市名称获取城市代码"""
        with session_scope() as session:
            statement = select(CityModel.city_code).where(CityModel.city_name == city_name)
            result = session.exec(statement).first()
            return result

    def update_city_province(self, city_code: str, province_code: str, province_name: Optional[str]) -> bool:
        """更新城市所属省份"""
        with session_scope() as session:
            statement = select(CityModel).where(CityModel.city_code == city_code)
            city = session.exec(statement).first()
            
            if not city:
                return False
            
            city.province_code = province_code
            city.province_name = province_name
            city.updated_at = func.now() # Though SQLModel handles this if updated_at is properly set, explicit is fine too
            
            session.add(city)
            session.commit()
            return True

    def get_city_codes(self) -> List[str]:
        """获取所有城市代码"""
        with session_scope() as session:
            statement = select(CityModel.city_code)
            return list(session.exec(statement).all())

    def get_province_map(self) -> Dict[str, str]:
        """获取省份代码到名称的映射"""
        with session_scope() as session:
            statement = select(ProvinceModel.province_code, ProvinceModel.province_name)
            results = session.exec(statement).all()
            return {r[0]: r[1] for r in results}
            
    def get_cities_grouped_by_province(self) -> List[CityModel]:
        """获取所有城市数据用于分组统计"""
        # 实际上复用 get_all_cities 即可，排序在内存做或者 SQL 做都行
        # 这里为了保持和原逻辑一致 (ORDER BY province_code, city_code)
        with session_scope() as session:
            statement = select(CityModel).where(CityModel.province_code != None).order_by(CityModel.province_code, CityModel.city_code)
            results = session.exec(statement).all()
            return [CityModel.model_validate(r) for r in results]


# 全局单例
region_repo = RegionRepository()
