"""
配置管理模块
负责从数据库中读取和更新系统配置
"""
import os
import sys
import json
import time
import pymysql
from typing import Dict, Any, Optional, Union
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import log
from db.mysql_manager import MySQLManager


class ConfigManager:
    """配置管理器，用于从数据库中读取和更新系统配置"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.mysql = MySQLManager()
        self.config_cache = {}
        self.last_refresh_time = 0
        self.cache_ttl = 300  # 缓存有效期（秒）
        
        # 初始加载配置
        self.refresh_cache()
    
    def refresh_cache(self) -> bool:
        """刷新配置缓存"""
        try:
            # 从数据库加载所有配置
            query = "SELECT config_key, config_value FROM system_config"
            results = self.mysql.fetch_all(query)
            
            if results:
                # 更新缓存
                new_cache = {}
                for row in results:
                    key = row['config_key']
                    value = row['config_value']
                    
                    # 尝试将JSON字符串转换为Python对象
                    try:
                        value = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        # 如果不是有效的JSON，保留原始字符串
                        pass
                    
                    new_cache[key] = value
                
                self.config_cache = new_cache
                self.last_refresh_time = time.time()
                log.debug(f"配置缓存已刷新，共加载 {len(self.config_cache)} 项配置")
                return True
            else:
                log.warning("未从数据库加载到任何配置")
                return False
                
        except Exception as e:
            log.error(f"刷新配置缓存失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        参数:
            key: 配置键
            default: 默认值，如果配置不存在则返回此值
            
        返回:
            配置值或默认值
        """
        # 检查缓存是否过期
        if time.time() - self.last_refresh_time > self.cache_ttl:
            self.refresh_cache()
        
        return self.config_cache.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """
        设置配置项
        
        参数:
            key: 配置键
            value: 配置值
            
        返回:
            bool: 是否设置成功
        """
        try:
            # 将复杂对象转换为JSON字符串
            if not isinstance(value, (str, int, float, bool)) and value is not None:
                value_str = json.dumps(value)
            else:
                value_str = str(value)
            
            # 更新或插入配置
            query = """
                INSERT INTO system_config (config_key, config_value) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE config_value = %s, update_time = NOW()
            """
            self.mysql.execute_query(query, (key, value_str, value_str))
            
            # 更新缓存
            self.config_cache[key] = value
            
            log.info(f"配置已更新: {key}")
            return True
            
        except Exception as e:
            log.error(f"更新配置失败: {key} - {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        删除配置项
        
        参数:
            key: 配置键
            
        返回:
            bool: 是否删除成功
        """
        try:
            query = "DELETE FROM system_config WHERE config_key = %s"
            result = self.mysql.execute_query(query, (key,))
            
            # 从缓存中移除
            if key in self.config_cache:
                del self.config_cache[key]
            
            log.info(f"配置已删除: {key}")
            return True
            
        except Exception as e:
            log.error(f"删除配置失败: {key} - {e}")
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置项
        
        返回:
            Dict[str, Any]: 所有配置项的字典
        """
        # 检查缓存是否过期
        if time.time() - self.last_refresh_time > self.cache_ttl:
            self.refresh_cache()
        
        return self.config_cache.copy()
    
    def get_by_prefix(self, prefix: str) -> Dict[str, Any]:
        """
        获取指定前缀的所有配置项
        
        参数:
            prefix: 配置键前缀
            
        返回:
            Dict[str, Any]: 匹配前缀的配置项字典
        """
        # 检查缓存是否过期
        if time.time() - self.last_refresh_time > self.cache_ttl:
            self.refresh_cache()
        
        return {k: v for k, v in self.config_cache.items() if k.startswith(prefix)}
    
    def init_default_configs(self) -> None:
        """初始化默认配置"""
        default_configs = {
            # API配置
            'api.host': '0.0.0.0',
            'api.port': 5001,
            'api.debug': False,
            'api.cors_origins': '*',
            
            # 任务配置
            'task.max_concurrent_tasks': 5,
            'task.queue_check_interval': 10,
            'task.default_priority': 5,
            'task.max_retry_count': 3,
            'task.retry_delay': 300,
            
            # 爬虫配置
            'spider.min_interval': 1.8,
            'spider.max_interval': 2.0,
            'spider.retry_times': 2,
            'spider.timeout': 15,
            'spider.max_workers': 10,
            'spider.user_agent_rotation': True,
            'spider.proxy_enabled': False,
            
            # Cookie配置
            'cookie.min_available_count': 3,
            'cookie.block_cooldown': 1800,
            'cookie.rotation_strategy': 'round_robin',
            'cookie.max_usage_per_day': 1000,
            
            # 输出配置
            'output.default_format': 'csv',
            'output.csv_encoding': 'utf-8-sig',
        }
        
        for key, value in default_configs.items():
            if self.get(key) is None:
                self.set(key, value)
        
        log.info(f"默认配置初始化完成，共设置 {len(default_configs)} 项配置")


# 创建全局实例
config_manager = ConfigManager() 