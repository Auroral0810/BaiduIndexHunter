#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
区域数据管理模块
管理百度指数城市代码相关的数据，提供查询接口
"""

import json
import redis
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

from src.core.config import REDIS_CONFIG
from src.core.logger import log
from src.data.repositories.region_repository import region_repo

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RegionManager:
    """区域数据管理类"""
    
    # Redis键前缀
    REDIS_KEY_PREFIX = "baidu_index:region:"
    
    # Redis键名
    REDIS_PROVINCES_KEY = "baidu_index:provinces"    # 省份数据
    REDIS_CITIES_KEY = "baidu_index:cities"          # 地级市数据
    REDIS_REGIONS_KEY = "baidu_index:regions"        # 区域关系数据
    REDIS_PROVINCE_CITIES_KEY = "baidu_index:province_cities"  # 省份下属城市数据
    
    # Redis过期时间（7天）
    REDIS_EXPIRE = 60 * 60 * 24 * 7
    
    def __init__(self):
        """初始化区域管理器"""
        self.redis_config = REDIS_CONFIG
        self.redis_client = None
        self.repo = region_repo
        self._connect()
    
    def _connect(self):
        """连接Redis"""
        try:
            # 连接Redis
            self.redis_client = redis.Redis(
                host=self.redis_config['host'],
                port=self.redis_config['port'],
                db=self.redis_config['db'],
                password=self.redis_config['password'],
                decode_responses=True  # 自动将字节解码为字符串
            )
            
            log.info("成功连接到Redis")
        except Exception as e:
            log.error(f"连接Redis失败: {e}")
            raise
    
    def disconnect(self):
        """断开连接"""
        if self.redis_client:
            self.redis_client.close()
        log.info("已断开Redis连接")
    
    def sync_to_redis(self):
        """将MySQL中的区域数据同步到Redis"""
        try:
            log.info("开始同步区域数据到Redis...")
            
            # 同步省份数据（包含大区信息）
            self._sync_provinces()
            
            # 同步地级市数据
            self._sync_cities()
            
            # 同步区域关系数据
            self._sync_regions()
            
            # 同步省份城市关系数据
            self.sync_province_cities()
            
            # log.info("区域数据同步到Redis完成")
            return True
        except Exception as e:
            log.error(f"同步区域数据到Redis失败: {e}")
            return False
    
    def _sync_provinces(self):
        """同步省份数据到Redis（包含大区信息）"""
        try:
            provinces = self.repo.get_all_provinces()
            
            provinces_data = {}
            for province in provinces:
                provinces_data[province.province_code] = {
                    'code': province.province_code,
                    'name': province.province_name,
                    'region': province.region_name or ''
                }
            
            # 存储为JSON字符串
            if provinces_data:
                self.redis_client.set(self.REDIS_PROVINCES_KEY, json.dumps(provinces_data, ensure_ascii=False))
                self.redis_client.expire(self.REDIS_PROVINCES_KEY, self.REDIS_EXPIRE)
            
            log.info(f"成功同步 {len(provinces_data)} 条省份数据到Redis")
        except Exception as e:
            log.error(f"Sync provinces failed: {e}")
    
    def _sync_cities(self):
        """同步地级市数据到Redis"""
        try:
            cities = self.repo.get_all_cities()
            
            cities_data = {}
            for city in cities:
                cities_data[city.city_code] = {
                    'code': city.city_code,
                    'name': city.city_name,
                    'province_code': city.province_code,
                    'province_name': city.province_name
                }
            
            # 存储为JSON字符串
            if cities_data:
                self.redis_client.set(self.REDIS_CITIES_KEY, json.dumps(cities_data, ensure_ascii=False))
                self.redis_client.expire(self.REDIS_CITIES_KEY, self.REDIS_EXPIRE)
            
            log.info(f"成功同步 {len(cities_data)} 条地级市数据到Redis")
        except Exception as e:
            log.error(f"Sync cities failed: {e}")
    
    def _sync_regions(self):
        """同步区域关系数据到Redis"""
        try:
            regions = self.repo.get_all_regions()
            children_relations = self.repo.get_all_children_relations()
            
            regions_data = {}
            children_map = {}
            
            # 构建父子关系映射
            for relation in children_relations:
                parent_code = relation.parent_code
                child_code = relation.child_code
                
                if parent_code not in children_map:
                    children_map[parent_code] = []
                children_map[parent_code].append(child_code)
            
            # 构建完整区域数据
            for region in regions:
                region_code = region.region_code
                # 基本信息
                region_data = {
                    'code': region_code,
                    'name': region.region_name,
                    'level': region.layer_level,
                    'parent_code': region.parent_code or '',
                    'children': children_map.get(region_code, [])
                }
                regions_data[region_code] = region_data
            
            # 补充父区域名称
            for region_code, region_data in regions_data.items():
                parent_code = region_data['parent_code']
                if parent_code and parent_code in regions_data:
                    region_data['parent_name'] = regions_data[parent_code]['name']
                else:
                    region_data['parent_name'] = ''
            
            # 存储为JSON字符串
            if regions_data:
                self.redis_client.set(self.REDIS_REGIONS_KEY, json.dumps(regions_data, ensure_ascii=False))
                self.redis_client.expire(self.REDIS_REGIONS_KEY, self.REDIS_EXPIRE)
            
            log.info(f"成功同步 {len(regions_data)} 条区域关系数据到Redis")
        except Exception as e:
            log.error(f"Sync regions failed: {e}")
    
    def get_all_provinces(self) -> Dict:
        """
        获取所有省份数据（包含大区信息）
        :return: 省份数据字典
        """
        provinces_json = self.redis_client.get(self.REDIS_PROVINCES_KEY)
        
        if provinces_json:
            return json.loads(provinces_json)
        
        # Redis中没有，同步数据并重新获取
        self._sync_provinces()
        provinces_json = self.redis_client.get(self.REDIS_PROVINCES_KEY)
        return json.loads(provinces_json) if provinces_json else {}
    
    def get_all_cities(self) -> Dict:
        """
        获取所有地级市数据
        :return: 地级市数据字典
        """
        cities_json = self.redis_client.get(self.REDIS_CITIES_KEY)
        
        if cities_json:
            return json.loads(cities_json)
        
        # Redis中没有，同步数据并重新获取
        self._sync_cities()
        cities_json = self.redis_client.get(self.REDIS_CITIES_KEY)
        return json.loads(cities_json) if cities_json else {}
    
    def get_all_regions(self) -> Dict:
        """
        获取所有区域关系数据
        :return: 区域关系数据字典
        """
        regions_json = self.redis_client.get(self.REDIS_REGIONS_KEY)
        
        if regions_json:
            return json.loads(regions_json)
        
        # Redis中没有，同步数据并重新获取
        self._sync_regions()
        regions_json = self.redis_client.get(self.REDIS_REGIONS_KEY)
        return json.loads(regions_json) if regions_json else {}
    
    def get_region_by_code(self, code: str) -> Optional[Dict]:
        """
        根据区域代码获取区域信息
        :param code: 区域代码
        :return: 区域信息字典
        """
        # 确保 code 为字符串
        code_str = str(code)
        
        # 从区域关系数据中获取
        regions = self.get_all_regions()
        return regions.get(code_str)
    
    def get_region_code_by_name(self, name: str, level: Optional[int] = None) -> Optional[str]:
        """
        根据区域名称获取区域代码
        """
        try:
            return self.repo.get_region_code_by_name(name, level)
        except Exception as e:
            log.error(f"获取区域代码失败: {e}")
            return None
    
    def get_city_name_by_code(self, city_code: str) -> Optional[str]:
        """
        根据城市代码获取城市名称
        """
        # 从地级市数据中获取
        cities = self.get_all_cities()
        city = cities.get(city_code)
        return city['name'] if city else None
    
    
    def get_province_region(self, province_code: str) -> Optional[str]:
        """
        获取省份所属的大区
        """
        try:
            return self.repo.get_province_region_name(province_code)
        except Exception as e:
            log.error(f"获取省份大区失败: {e}")
            return None
    
    def get_region_provinces(self, region_name: str) -> List[Dict]:
        """
        获取大区下属的所有省份
        """
        try:
            log.info(f"开始查询大区 '{region_name}' 下属的省份")
            
            # 先检查Redis中是否有此大区的省份数据
            provinces_data = self.get_all_provinces()
            region_provinces = []
            
            # 从缓存中筛选
            for code, province in provinces_data.items():
                if province.get('region') == region_name:
                    province_info = {
                        'code': code,
                        'name': province['name'],
                        'level': 1  # 省级默认为1级
                    }
                    region_provinces.append(province_info)
            
            # 如果Redis中找到了数据，直接返回
            if region_provinces:
                # log.info(f"从Redis缓存中找到大区 '{region_name}' 的 {len(region_provinces)} 个省份")
                return region_provinces
            
            # Redis中没找到，从数据库查询
            log.info(f"Redis中未找到大区 '{region_name}' 数据，尝试从数据库查询")
            
            provinces = self.repo.get_provinces_by_region(region_name)
            
            if provinces:
                log.info(f"从数据库找到大区 '{region_name}' 的 {len(provinces)} 个省份")
                # 更新Redis缓存
                self._sync_provinces()
                return provinces
            
            log.warning(f"数据库中未找到大区 '{region_name}' 的省份数据")
            return []
        except Exception as e:
            log.error(f"获取大区省份失败: {e}")
            return []
    
    def get_region_children(self, parent_code: str) -> List[Dict]:
        """
        获取区域的直接子区域
        """
        # 从区域关系数据中获取
        regions = self.get_all_regions()
        parent_region = regions.get(parent_code)
        
        if not parent_region or not parent_region.get('children'):
            return []
        
        children = []
        for child_code in parent_region['children']:
            child_region = regions.get(child_code)
            if child_region:
                children.append(child_region)
        
        return children
    
    def get_region_all_children(self, parent_code: str) -> List[Dict]:
        """
        递归获取区域的所有子区域（包括子区域的子区域）
        """
        # 先获取直接子区域
        direct_children = self.get_region_children(parent_code)
        all_children = direct_children.copy()
        
        # 递归获取每个子区域的子区域
        for child in direct_children:
            child_code = child['code']
            grandchildren = self.get_region_all_children(child_code)
            all_children.extend(grandchildren)
        
        return all_children
    
    def get_region_path(self, code: str) -> List[Dict]:
        """
        获取区域的完整路径（从顶级区域到当前区域）
        """
        path = []
        regions = self.get_all_regions()
        current_code = code
        
        # 防止无限循环
        max_iterations = 10
        iterations = 0
        
        while current_code and iterations < max_iterations:
            region = regions.get(current_code)
            if not region:
                break
            
            path.insert(0, region)  # 插入到开头
            current_code = region.get('parent_code')
            
            iterations += 1
        
        return path

    def get_city_code_by_name(self, city_name: str) -> Optional[str]:
        """
        根据城市名称获取城市代码
        """
        if not city_name:
            log.warning("传入的城市名称为空")
            return None
            
        # log.info(f"开始查询城市名称 '{city_name}' 对应的代码")
        
        # 先从Redis缓存中查找
        cities = self.get_all_cities()
        
        # 遍历城市数据查找匹配名称的城市
        for code, city in cities.items():
            if city["name"] == city_name:
                # log.info(f"从Redis缓存中找到城市: '{city_name}', 代码: {code}")
                return code
        
        # Redis中没找到，从数据库查询
        try:
            log.info(f"Redis中未找到城市: '{city_name}', 尝试从数据库查询")
            city_code = self.repo.get_city_code_by_name(city_name)
            
            if city_code:
                # 更新Redis缓存
                self._sync_cities()
                log.info(f"从数据库找到城市: '{city_name}', 代码: {city_code}, 并更新了Redis缓存")
                return city_code
            
            log.warning(f"数据库中未找到城市: '{city_name}'")
            return None
        except Exception as e:
            log.error(f"获取城市代码失败: {e}")
            return None

    def update_city_province(self, city_code: str, province_code: str, province_name: Optional[str] = None) -> bool:
        """
        更新城市的所属省份信息
        """
        try:
            # 检查城市是否存在
            city_name = self.get_city_name_by_code(city_code)
            if not city_name:
                log.warning(f"更新失败，城市代码不存在: {city_code}")
                return False
            
            # 如果没有提供省份名称，尝试获取
            if not province_name:
                province_info = self.get_region_by_code(province_code)
                if province_info:
                    province_name = province_info.get('name')
                else:
                    # 尝试从 Repo 获取
                    province_name = self.repo.get_province_region_name(province_code) or ""
            
            # 如果省份名称仍为空，记录警告但继续执行
            if not province_name:
                log.warning(f"未能获取省份名称，仅更新省份代码: {province_code}")
            
            # 更新数据库
            success = self.repo.update_city_province(city_code, province_code, province_name)
            
            if not success:
               log.warning(f"更新失败，城市代码可能不存在: {city_code}")
               return False
            
            log.info(f"成功更新城市所属省份: 城市={city_code}, 省份={province_code}")
            
            # 更新Redis缓存
            self._sync_cities()
            
            return True
                
        except Exception as e:
            log.error(f"更新城市所属省份失败: {e}")
            return False

    def batch_update_city_province(self, cities: List[Dict]) -> Tuple[int, int, int]:
        """
        批量更新城市的所属省份信息
        Returns:
            Tuple[int, int, int]: (总数, 成功数, 失败数)
        """
        success_count = 0
        failed_count = 0
        total = len(cities)
        
        for city_data in cities:
            city_code = city_data.get('city_code')
            province_code = city_data.get('province_code')
            province_name = city_data.get('province_name')
            
            if not city_code or not province_code:
                failed_count += 1
                continue
            
            # 这里的 update_city_province 内部已经包含了如果没有province_name则自动查找的逻辑
            result = self.update_city_province(city_code, province_code, province_name)
            
            if result:
                success_count += 1
            else:
                failed_count += 1
                
        return total, success_count, failed_count
    
    def sync_city_province(self) -> Optional[Tuple[int, int, int]]:
        """
        根据region_children表同步所有城市的所属省份信息
        """
        # 注意：此方法逻辑较复杂，涉及多表关联。
        # 这里我们利用 Repository 获取需要的数据然后在内存处理，
        # 或者在 Repo 中增加复杂查询的方法。
        # 为保持 Service 逻辑清晰，我们在 Repo 中并不实现这个巨大的业务逻辑，
        # 而是分别获取数据。
        
        try:
            log.info("开始同步城市所属省份信息...")
            
            # 获取省份映射
            provinces = self.repo.get_province_map()
            
            # 获取所有区域父子关系
            children_relations = self.repo.get_all_children_relations()
            
            # 筛选出 父=省, 子=市 的关系
            # 在 memory 中处理比在 DB 中再写一遍 JOIN 简单，且数据量不大
            city_provinces = {}
            for rel in children_relations:
                parent_code = rel.parent_code
                child_code = rel.child_code
                
                if parent_code in provinces:
                    city_provinces[child_code] = {
                        'province_code': parent_code,
                        'province_name': provinces[parent_code]
                    }

            # 获取所有城市代码
            cities = self.repo.get_city_codes()
            
            total = len(cities)
            success_count = 0
            failed_count = 0
            
            # 更新城市所属省份
            for city_code in cities:
                if city_code in city_provinces:
                    province_data = city_provinces[city_code]
                    result = self.update_city_province(
                        city_code,
                        province_data['province_code'],
                        province_data['province_name']
                    )
                    if result:
                        success_count += 1
                    else:
                        failed_count += 1
                else:
                    # log.warning(f"城市 {city_code} 没有找到对应的省份关系")
                    failed_count += 1
            
            # 更新Redis缓存
            self._sync_cities()
            
            log.info(f"城市所属省份同步完成，总数: {total}, 成功: {success_count}, 失败: {failed_count}")
            return total, success_count, failed_count
            
        except Exception as e:
            log.error(f"同步城市所属省份失败: {e}")
            import traceback
            log.error(traceback.format_exc())
            return None

    def sync_province_cities(self) -> bool:
        """
        统计每个省份下面的地级市和代码，并保存到Redis
        """
        try:
            province_cities = {}
            
            # 从 Repo 获取所有城市数据（已按省份排序）
            cities = self.repo.get_cities_grouped_by_province()
            
            for city in cities:
                province_code = city.province_code
                province_name = city.province_name
                city_code = city.city_code
                city_name = city.city_name
                
                # 如果省份不在字典中，初始化
                if province_code not in province_cities:
                    province_cities[province_code] = {
                        'province_code': province_code,
                        'province_name': province_name,
                        'city_count': 0,
                        'cities': {}
                    }
                
                # 添加城市到对应省份
                province_cities[province_code]['cities'][city_code] = {
                    'code': city_code,
                    'name': city_name
                }
                province_cities[province_code]['city_count'] += 1
            
            # 存储为JSON字符串
            if province_cities:
                self.redis_client.set(
                    self.REDIS_PROVINCE_CITIES_KEY, 
                    json.dumps(province_cities, ensure_ascii=False)
                )
                self.redis_client.expire(self.REDIS_PROVINCE_CITIES_KEY, self.REDIS_EXPIRE)
                
                log.info(f"成功统计并同步 {len(province_cities)} 个省份的城市数据到Redis")
                return True
            else:
                log.warning("未找到任何省份城市关系数据")
                return False
                
        except Exception as e:
            log.error(f"统计各省份下属城市数据失败: {e}")
            return False
    
    def get_province_cities(self, province_code: Optional[str] = None) -> Dict:
        """
        获取各省份下属城市数据
        """
        province_cities_json = self.redis_client.get(self.REDIS_PROVINCE_CITIES_KEY)
        
        # 如果Redis中没有数据，先同步
        if not province_cities_json:
            self.sync_province_cities()
            province_cities_json = self.redis_client.get(self.REDIS_PROVINCE_CITIES_KEY)
            
        if not province_cities_json:
            return {}
            
        province_cities = json.loads(province_cities_json)
        
        # 如果指定了省份代码，只返回该省份的数据
        if province_code:
            return {province_code: province_cities.get(province_code)} if province_code in province_cities else {}
        
        return province_cities


# 创建单例实例
region_manager = RegionManager()

# 提供获取实例的函数
def get_region_manager():
    """获取RegionManager实例"""
    return region_manager
