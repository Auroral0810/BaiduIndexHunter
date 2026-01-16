#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON数据导入MySQL脚本
将百度指数城市代码相关的JSON文件导入到MySQL数据库中
"""

import json
import mysql.connector
import os
from mysql.connector import Error
from typing import Dict, List, Any
import logging
import os
import multiprocessing
from dotenv import load_dotenv
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
import pymysql

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# 数据库配置
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', '123456'),
    'db': os.getenv('MYSQL_DB', 'BaiduIndexHunter'),
}

class RegionDataImporter:
    def __init__(self, host=None, user=None, password=None, database=None):
        """初始化数据库连接配置"""
        
        # 使用传入的参数或默认从配置文件获取
        self.config = {
            'host': host or MYSQL_CONFIG['host'],
            'user': user or MYSQL_CONFIG['user'],
            'password': password or MYSQL_CONFIG['password'],
            'database': database or MYSQL_CONFIG['db'],
            'charset': 'utf8mb4'
        }
        self.connection = None
        
    def connect(self):
        """连接数据库"""
        try:
            self.connection = pymysql.connect(
                host=self.config['host'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database'],
                charset=self.config['charset'],
                cursorclass=pymysql.cursors.DictCursor
            )
            if self.connection.open:
                logger.info("成功连接到MySQL数据库")
                return True
        except Exception as e:
            logger.error(f"连接数据库失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection and self.connection.open:
            self.connection.close()
            logger.info("数据库连接已断开")
    
    def load_json_file(self, file_path: str) -> Dict[str, Any]:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"成功加载文件: {file_path}")
                return data
        except Exception as e:
            logger.error(f"加载文件失败 {file_path}: {e}")
            return {}
    
    def clear_tables(self):
        """清空所有表数据（按依赖关系顺序）"""
        try:
            cursor = self.connection.cursor()
            # 按照外键依赖关系的逆序删除
            tables = ['region_children', 'prefecture_city', 'province_region', 'region_hierarchy']
            
            # 暂时禁用外键检查
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
                logger.info(f"清空表 {table}")
            
            # 重新启用外键检查
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            cursor.close()
            
        except Exception as e:
            logger.error(f"清空表失败: {e}")
    
    def import_region_hierarchy(self, allcitycode_data: Dict, layer_data: Dict, parent_data: Dict):
        """导入区域层级表 - 使用两步插入法解决自引用外键约束问题"""
        try:
            cursor = self.connection.cursor()
            
            # 第一步：先插入所有记录，但parent_code设为NULL
            insert_data_step1 = []
            for code, name in allcitycode_data.items():
                layer = layer_data.get(code, 1)  # 默认层级为1
                # 第一步先不设置parent_code
                insert_data_step1.append((code, name, layer, None))
            
            # 批量插入 - 第一步
            insert_sql = """
                INSERT INTO region_hierarchy (region_code, region_name, layer_level, parent_code)
                VALUES (%s, %s, %s, %s)
            """
            
            cursor.executemany(insert_sql, insert_data_step1)
            self.connection.commit()
            logger.info(f"第一步：成功导入区域层级基础数据: {len(insert_data_step1)} 条记录")
            
            # 第二步：更新所有记录的parent_code
            update_data = []
            for code in allcitycode_data.keys():
                parent_code = parent_data.get(code)  # 可能为None
                if parent_code:  # 只更新有父节点的记录
                    update_data.append((parent_code, code))
            
            # 批量更新 - 第二步
            if update_data:
                update_sql = """
                    UPDATE region_hierarchy 
                    SET parent_code = %s 
                    WHERE region_code = %s
                """
                cursor.executemany(update_sql, update_data)
                self.connection.commit()
                logger.info(f"第二步：成功更新区域层级父节点数据: {len(update_data)} 条记录")
            
            cursor.close()
            
        except Exception as e:
            logger.error(f"导入区域层级数据失败: {e}")
            self.connection.rollback()
    
    def import_province_region(self, province_data: Dict, region_data: Dict):
        """导入省份区域表"""
        try:
            cursor = self.connection.cursor()
            
            # 准备数据
            insert_data = []
            for code, name in province_data.items():
                region_name = region_data.get(code)  # 可能为None
                insert_data.append((code, name, region_name))
            
            # 批量插入
            insert_sql = """
                INSERT INTO province_region (province_code, province_name, region_name)
                VALUES (%s, %s, %s)
            """
            
            cursor.executemany(insert_sql, insert_data)
            self.connection.commit()
            logger.info(f"成功导入省份区域数据: {len(insert_data)} 条记录")
            cursor.close()
            
        except Exception as e:
            logger.error(f"导入省份区域数据失败: {e}")
            self.connection.rollback()
    
    def import_prefecture_city(self, city_data: Dict):
        """导入地级市表"""
        try:
            cursor = self.connection.cursor()
            
            # 准备数据
            insert_data = [(code, name) for code, name in city_data.items()]
            
            # 批量插入
            insert_sql = """
                INSERT INTO prefecture_city (city_code, city_name)
                VALUES (%s, %s)
            """
            
            cursor.executemany(insert_sql, insert_data)
            self.connection.commit()
            logger.info(f"成功导入地级市数据: {len(insert_data)} 条记录")
            cursor.close()
            
        except Exception as e:
            logger.error(f"导入地级市数据失败: {e}")
            self.connection.rollback()
    
    def import_region_children(self, children_data: Dict):
        """导入区域子节点关系表"""
        try:
            cursor = self.connection.cursor()
            
            # 准备数据
            insert_data = []
            for parent_code, children_list in children_data.items():
                for sort_order, child_code in enumerate(children_list):
                    insert_data.append((parent_code, str(child_code), sort_order))
            
            # 批量插入
            insert_sql = """
                INSERT INTO region_children (parent_code, child_code, sort_order)
                VALUES (%s, %s, %s)
            """
            
            cursor.executemany(insert_sql, insert_data)
            self.connection.commit()
            logger.info(f"成功导入区域子节点关系数据: {len(insert_data)} 条记录")
            cursor.close()
            
        except Exception as e:
            logger.error(f"导入区域子节点关系数据失败: {e}")
            self.connection.rollback()
    
    def test_data_query(self):
        """测试数据查询"""
        try:
            cursor = self.connection.cursor()
            
            # 测试1：查询所有表的记录数
            tables = ['region_hierarchy', 'province_region', 'prefecture_city', 'region_children']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                result = cursor.fetchone()
                logger.info(f"表 {table} 记录数: {result['count']}")
            
            # 测试2：查询层级为1的区域（省级）
            cursor.execute("""
                SELECT region_code, region_name, layer_level 
                FROM region_hierarchy 
                WHERE layer_level = 1 
                LIMIT 5
            """)
            results = cursor.fetchall()
            logger.info("省级区域示例:")
            for row in results:
                logger.info(f"  {row['region_code']}: {row['region_name']}")
            
            # 测试3：验证层级关系
            cursor.execute("""
                SELECT rh.region_code, rh.region_name, rh.layer_level, 
                       p.region_code as parent_code, p.region_name as parent_name
                FROM region_hierarchy rh
                JOIN region_hierarchy p ON rh.parent_code = p.region_code
                WHERE rh.layer_level = 2
                LIMIT 5
            """)
            results = cursor.fetchall()
            logger.info("层级关系示例(省-市):")
            for row in results:
                logger.info(f"  {row['region_code']}({row['region_name']}) -> {row['parent_code']}({row['parent_name']})")
            
            # 测试4：验证大区-省份关系
            cursor.execute("""
                SELECT p.province_code, p.province_name, p.region_name
                FROM province_region p
                WHERE p.region_name IS NOT NULL
                LIMIT 5
            """)
            results = cursor.fetchall()
            logger.info("大区-省份关系示例:")
            for row in results:
                logger.info(f"  {row['province_code']}({row['province_name']}) -> {row['region_name']}")
            
            cursor.close()
        except Exception as e:
            logger.error(f"测试数据查询失败: {e}")

    def run(self, data_dir: str):
        """运行导入程序"""
        try:
            # 连接数据库
            if not self.connect():
                return False
            
            # 定义文件名映射关系
            file_mappings = {
                'allcitycode': 'allcitycode.json',
                'layer': 'citycode-layer.json',
                'parent': '城市所属的上级区域.json',
                'province': 'code-province.json',
                'region': 'code-diqu.json',
                'city': 'code-city.json',
                'children': 'citycode-soncitycode.json'
            }
            
            # 加载所有JSON文件
            allcitycode_path = os.path.join(data_dir, file_mappings['allcitycode'])
            layer_path = os.path.join(data_dir, file_mappings['layer'])
            parent_path = os.path.join(data_dir, file_mappings['parent'])
            province_path = os.path.join(data_dir, file_mappings['province'])
            region_path = os.path.join(data_dir, file_mappings['region'])
            city_path = os.path.join(data_dir, file_mappings['city'])
            children_path = os.path.join(data_dir, file_mappings['children'])
            
            allcitycode_data = self.load_json_file(allcitycode_path)
            layer_data = self.load_json_file(layer_path)
            parent_data = self.load_json_file(parent_path)
            province_data = self.load_json_file(province_path)
            region_data = self.load_json_file(region_path)
            city_data = self.load_json_file(city_path)
            children_data = self.load_json_file(children_path)
            
            if not all([allcitycode_data, layer_data, parent_data, province_data, 
                     region_data, city_data, children_data]):
                logger.error("一个或多个JSON文件加载失败")
                return False
            
            # 清空所有表
            self.clear_tables()
            
            # 导入数据
            self.import_region_hierarchy(allcitycode_data, layer_data, parent_data)
            self.import_province_region(province_data, region_data)
            self.import_prefecture_city(city_data)
            self.import_region_children(children_data)
            
            # 测试查询
            self.test_data_query()
            
            # 断开连接
            self.disconnect()
            
            logger.info("区域数据导入完成")
            return True
        except Exception as e:
            logger.error(f"导入程序运行失败: {e}")
            return False

if __name__ == "__main__":
    # 尝试两个不同的数据目录
    DATA_DIR_JOSN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "josn")
    DATA_DIR_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    
    # 首先尝试josn目录
    importer = RegionDataImporter()
    success = importer.run(DATA_DIR_JOSN)
    
    # 如果josn目录失败，尝试data目录
    if not success:
        print("从josn目录导入失败，尝试从data目录导入...")
        success = importer.run(DATA_DIR_DATA)
    
    if success:
        print("区域数据导入成功!")
    else:
        print("区域数据导入失败，请查看日志获取详细信息。")