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
import pymysql
from core.config import config

# 从 config 获取配置
MYSQL_CONFIG = config.mysql_config
REDIS_CONFIG = config.redis_config
from utils.logger import log
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
        self.mysql_config = MYSQL_CONFIG
        self.redis_config = REDIS_CONFIG
        self.redis_client = None
        self.mysql_conn = None
        self._connect()
    
    def _connect(self):
        """连接数据库和Redis"""
        try:
            # 连接MySQL
            self.mysql_conn = pymysql.connect(
                host=self.mysql_config['host'],
                user=self.mysql_config['user'],
                password=self.mysql_config['password'],
                database=self.mysql_config['db'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            # 连接Redis
            self.redis_client = redis.Redis(
                host=self.redis_config['host'],
                port=self.redis_config['port'],
                db=self.redis_config['db'],
                password=self.redis_config['password'],
                decode_responses=True  # 自动将字节解码为字符串
            )
            
            log.info("成功连接到MySQL和Redis")
        except Exception as e:
            log.error(f"连接数据库或Redis失败: {e}")
            raise
    
    def disconnect(self):
        """断开连接"""
        if self.mysql_conn:
            self.mysql_conn.close()
        if self.redis_client:
            self.redis_client.close()
        log.info("已断开数据库和Redis连接")
    
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
        with self.mysql_conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    province_code as code, 
                    province_name as name, 
                    region_name as region
                FROM province_region
                ORDER BY province_code
            """)
            provinces = cursor.fetchall()
            
            provinces_data = {}
            for province in provinces:
                province_code = province['code']
                province_name = province['name']
                region_name = province['region']
                
                provinces_data[province_code] = {
                    'code': province_code,
                    'name': province_name,
                    'region': region_name or ''
                }
            
            # 存储为JSON字符串
            if provinces_data:
                self.redis_client.set(self.REDIS_PROVINCES_KEY, json.dumps(provinces_data, ensure_ascii=False))
                self.redis_client.expire(self.REDIS_PROVINCES_KEY, self.REDIS_EXPIRE)
            
            log.info(f"成功同步 {len(provinces_data)} 条省份数据到Redis")
    
    def _sync_cities(self):
        """同步地级市数据到Redis"""
        with self.mysql_conn.cursor() as cursor:
            cursor.execute("""
                SELECT city_code, city_name, province_code, province_name
                FROM prefecture_city 
                ORDER BY city_code
            """)
            cities = cursor.fetchall()
            
            cities_data = {}
            for city in cities:
                city_code = city['city_code']
                city_name = city['city_name']
                province_code = city['province_code']
                province_name = city['province_name']
                
                cities_data[city_code] = {
                    'code': city_code,
                    'name': city_name,
                    'province_code': province_code,
                    'province_name': province_name
                }
            
            # 存储为JSON字符串
            if cities_data:
                self.redis_client.set(self.REDIS_CITIES_KEY, json.dumps(cities_data, ensure_ascii=False))
                self.redis_client.expire(self.REDIS_CITIES_KEY, self.REDIS_EXPIRE)
            
            log.info(f"成功同步 {len(cities_data)} 条地级市数据到Redis")
    
    def _sync_regions(self):
        """同步区域关系数据到Redis"""
        with self.mysql_conn.cursor() as cursor:
            # 获取所有区域信息
            cursor.execute("""
                SELECT region_code, region_name, layer_level, parent_code
                FROM region_hierarchy
                ORDER BY layer_level, region_code
            """)
            regions = cursor.fetchall()
            
            # 获取所有父子关系
            cursor.execute("""
                SELECT parent_code, child_code
                FROM region_children
                ORDER BY parent_code, sort_order
            """)
            children_relations = cursor.fetchall()
            
            # 构建区域数据
            regions_data = {}
            children_map = {}
            
            # 构建父子关系映射
            for relation in children_relations:
                parent_code = relation['parent_code']
                child_code = relation['child_code']
                
                if parent_code not in children_map:
                    children_map[parent_code] = []
                children_map[parent_code].append(child_code)
            
            # 构建完整区域数据
            for region in regions:
                region_code = region['region_code']
                region_name = region['region_name']
                layer_level = region['layer_level']
                parent_code = region['parent_code']
                
                # 基本信息
                region_data = {
                    'code': region_code,
                    'name': region_name,
                    'level': layer_level,
                    'parent_code': parent_code or '',
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
        # 从区域关系数据中获取
        regions = self.get_all_regions()
        return regions.get(code)
    
    def get_region_code_by_name(self, name: str, level: Optional[int] = None) -> Optional[str]:
        """
        根据区域名称获取区域代码
        :param name: 区域名称
        :param level: 区域层级，如果有多个同名区域，可以指定层级
        :return: 区域代码
        """
        try:
            with self.mysql_conn.cursor() as cursor:
                # 构建SQL查询
                sql = "SELECT region_code FROM region_hierarchy WHERE region_name = %s"
                params = [name]
                
                # 如果指定了层级，添加层级条件
                if level is not None:
                    sql += " AND layer_level = %s"
                    params.append(level)
                
                # 执行查询
                cursor.execute(sql, params)
                result = cursor.fetchone()
                
                if result:
                    return result['region_code']
                return None
        except Exception as e:
            log.error(f"获取区域代码失败: {e}")
            return None
    
    def get_city_name_by_code(self, city_code: str) -> Optional[str]:
        """
        根据城市代码获取城市名称
        :param city_code: 城市代码
        :return: 城市名称
        """
        # 从地级市数据中获取
        cities = self.get_all_cities()
        city = cities.get(city_code)
        return city['name'] if city else None
    
    
    def get_province_region(self, province_code: str) -> Optional[str]:
        """
        获取省份所属的大区
        :param province_code: 省份代码
        :return: 大区名称
        """
        try:
            with self.mysql_conn.cursor() as cursor:
                # 直接查询省份大区表
                cursor.execute("SELECT region_name FROM province_region WHERE province_code = %s", [province_code])
                result = cursor.fetchone()
                
                if result and result['region_name']:
                    return result['region_name']
                return None
        except Exception as e:
            log.error(f"获取省份大区失败: {e}")
            return None
    
    def get_region_provinces(self, region_name: str) -> List[Dict]:
        """
        获取大区下属的所有省份
        :param region_name: 大区名称
        :return: 省份列表
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
                log.info(f"从Redis缓存中找到大区 '{region_name}' 的 {len(region_provinces)} 个省份")
                return region_provinces
            
            # Redis中没找到，从数据库查询
            log.info(f"Redis中未找到大区 '{region_name}' 数据，尝试从数据库查询")
            with self.mysql_conn.cursor() as cursor:
                # 直接查询省份大区表，获取指定大区下的所有省份
                cursor.execute("""
                    SELECT pr.province_code as code, pr.province_name as name, 
                           COALESCE(rh.layer_level, 1) as level
                    FROM province_region pr
                    LEFT JOIN region_hierarchy rh ON pr.province_code = rh.region_code
                    WHERE pr.region_name = %s
                """, [region_name])
                
                provinces = cursor.fetchall()
                
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
        :param parent_code: 父区域代码
        :return: 子区域列表
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
        :param parent_code: 父区域代码
        :return: 所有子区域列表
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
        :param code: 区域代码
        :return: 区域路径列表
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
        :param city_name: 城市名称
        :return: 城市代码
        """
        if not city_name:
            log.warning("传入的城市名称为空")
            return None
            
        log.info(f"开始查询城市名称 '{city_name}' 对应的代码")
        
        # 先从Redis缓存中查找
        cities = self.get_all_cities()
        
        # 遍历城市数据查找匹配名称的城市
        for code, city in cities.items():
            if city["name"] == city_name:
                log.info(f"从Redis缓存中找到城市: '{city_name}', 代码: {code}")
                return code
        
        # Redis中没找到，从数据库查询
        try:
            log.info(f"Redis中未找到城市: '{city_name}', 尝试从数据库查询")
            with self.mysql_conn.cursor() as cursor:
                cursor.execute("SELECT city_code FROM prefecture_city WHERE city_name = %s", [city_name])
                result = cursor.fetchone()
                
                if result:
                    city_code = result["city_code"]
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
        :param city_code: 城市代码
        :param province_code: 省份代码
        :param province_name: 省份名称（如果为None，将尝试从数据库获取）
        :return: 是否更新成功
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
                    # 尝试从province_region表获取
                    with self.mysql_conn.cursor() as cursor:
                        cursor.execute(
                            "SELECT province_name FROM province_region WHERE province_code = %s",
                            [province_code]
                        )
                        result = cursor.fetchone()
                        if result:
                            province_name = result['province_name']
            
            # 如果省份名称仍为空，记录警告但继续执行
            if not province_name:
                log.warning(f"未能获取省份名称，仅更新省份代码: {province_code}")
            
            # 更新数据库
            with self.mysql_conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE prefecture_city 
                    SET province_code = %s, province_name = %s, updated_at = NOW() 
                    WHERE city_code = %s
                    """,
                    [province_code, province_name, city_code]
                )
                self.mysql_conn.commit()
                
                if cursor.rowcount == 0:
                    log.warning(f"更新失败，城市代码可能不存在: {city_code}")
                    return False
                
                log.info(f"成功更新城市所属省份: 城市={city_code}, 省份={province_code}")
                
                # 更新Redis缓存
                self._sync_cities()
                
                return True
                
        except Exception as e:
            log.error(f"更新城市所属省份失败: {e}")
            return False
    
    def sync_city_province(self) -> Optional[Tuple[int, int, int]]:
        """
        根据region_children表同步所有城市的所属省份信息
        :return: 元组(总数, 成功数, 失败数)，失败时返回None
        """
        try:
            log.info("开始同步城市所属省份信息...")
            
            # 获取所有省级行政区
            provinces = {}
            with self.mysql_conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT province_code, province_name 
                    FROM province_region
                    """
                )
                for province in cursor.fetchall():
                    provinces[province['province_code']] = province['province_name']
            
            # 获取所有省份和城市的父子关系
            city_provinces = {}
            with self.mysql_conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT rc.parent_code, rc.child_code
                    FROM region_children rc
                    JOIN prefecture_city pc ON rc.child_code = pc.city_code
                    JOIN province_region pr ON rc.parent_code = pr.province_code
                    """
                )
                for relation in cursor.fetchall():
                    parent_code = relation['parent_code']
                    child_code = relation['child_code']
                    if parent_code in provinces:
                        city_provinces[child_code] = {
                            'province_code': parent_code,
                            'province_name': provinces[parent_code]
                        }
            
            # 获取所有需要更新的城市
            cities = []
            with self.mysql_conn.cursor() as cursor:
                cursor.execute("SELECT city_code FROM prefecture_city")
                for city in cursor.fetchall():
                    cities.append(city['city_code'])
            
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
                    log.warning(f"城市 {city_code} 没有找到对应的省份关系")
                    failed_count += 1
            
            # 更新Redis缓存
            self._sync_cities()
            
            log.info(f"城市所属省份同步完成，总数: {total}, 成功: {success_count}, 失败: {failed_count}")
            return total, success_count, failed_count
            
        except Exception as e:
            log.error(f"同步城市所属省份失败: {e}")
            return None

    def sync_province_cities(self) -> bool:
        """
        统计每个省份下面的地级市和代码，并保存到Redis
        :return: 是否同步成功
        """
        try:
            # log.info("开始统计各省份下属城市数据...")
            
            province_cities = {}
            
            # 从MySQL获取所有城市数据，按省份分组
            with self.mysql_conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        province_code, province_name, 
                        city_code, city_name
                    FROM prefecture_city
                    WHERE province_code IS NOT NULL
                    ORDER BY province_code, city_code
                """)
                
                cities = cursor.fetchall()
                
                # 按省份分组
                for city in cities:
                    province_code = city['province_code']
                    province_name = city['province_name']
                    city_code = city['city_code']
                    city_name = city['city_name']
                    
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
        :param province_code: 省份代码，如果提供则只返回该省份的数据
        :return: 省份城市数据字典
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
