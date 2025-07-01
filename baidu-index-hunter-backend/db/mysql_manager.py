"""
MySQL数据库连接管理模块
"""
import os
import sys
import time
import pymysql
from pymysql.cursors import DictCursor
from typing import List, Dict, Any, Optional, Union, Tuple

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import log
from config.settings import MYSQL_CONFIG


class MySQLManager:
    """MySQL数据库连接管理器"""
    
    def __init__(self, config=None):
        """
        初始化MySQL连接管理器
        
        参数:
            config: MySQL配置，如果为None则使用settings.py中的配置
        """
        self.config = MYSQL_CONFIG
        self.connection = None
        self.max_retries = 3
        self.retry_delay = 2  # 秒
        
        # 尝试建立连接
        self._connect()
    
    def _connect(self):
        """建立MySQL连接"""
        try:
            self.connection = pymysql.connect(
                host=self.config['host'],
                port=self.config.get('port', 3306),
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['db'],
                charset=self.config.get('charset', 'utf8mb4'),
                cursorclass=DictCursor,
                autocommit=True
            )
            log.info(f"MySQL连接成功: {self.config['host']}:{self.config.get('port', 3306)}/{self.config['db']}")
        except Exception as e:
            log.error(f"MySQL连接失败: {e}")
            self.connection = None
    
    def ensure_connection(self):
        """确保MySQL连接有效"""
        if self.connection is None:
            self._connect()
            return
        
        try:
            # 检查连接是否有效
            self.connection.ping(reconnect=False)
        except:
            log.warning("MySQL连接已断开，尝试重新连接")
            try:
                self.connection.close()
            except:
                pass
            self._connect()
    
    def execute_query(self, query: str, params: tuple = None) -> int:
        """
        执行SQL查询（INSERT, UPDATE, DELETE等）
        
        参数:
            query: SQL查询语句
            params: 查询参数
            
        返回:
            affected_rows: 受影响的行数
        """
        for attempt in range(self.max_retries):
            try:
                self.ensure_connection()
                if self.connection is None:
                    log.error("无法执行查询，MySQL连接失败")
                    return 0
                
                with self.connection.cursor() as cursor:
                    affected_rows = cursor.execute(query, params)
                    return affected_rows
            except pymysql.OperationalError as e:
                if attempt < self.max_retries - 1:
                    log.warning(f"MySQL操作错误，尝试重新连接: {e}")
                    try:
                        self.connection.close()
                    except:
                        pass
                    self.connection = None
                    time.sleep(self.retry_delay)
                else:
                    log.error(f"MySQL查询失败，已达到最大重试次数: {e}")
                    raise
            except Exception as e:
                log.error(f"MySQL查询执行失败: {e}")
                raise
        
        return 0
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        批量执行SQL查询
        
        参数:
            query: SQL查询语句
            params_list: 查询参数列表
            
        返回:
            affected_rows: 受影响的行数
        """
        if not params_list:
            return 0
            
        for attempt in range(self.max_retries):
            try:
                self.ensure_connection()
                if self.connection is None:
                    log.error("无法执行批量查询，MySQL连接失败")
                    return 0
                
                with self.connection.cursor() as cursor:
                    affected_rows = cursor.executemany(query, params_list)
                    return affected_rows
            except pymysql.OperationalError as e:
                if attempt < self.max_retries - 1:
                    log.warning(f"MySQL操作错误，尝试重新连接: {e}")
                    try:
                        self.connection.close()
                    except:
                        pass
                    self.connection = None
                    time.sleep(self.retry_delay)
                else:
                    log.error(f"MySQL批量查询失败，已达到最大重试次数: {e}")
                    raise
            except Exception as e:
                log.error(f"MySQL批量查询执行失败: {e}")
                raise
        
        return 0
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """
        执行查询并返回单条结果
        
        参数:
            query: SQL查询语句
            params: 查询参数
            
        返回:
            result: 查询结果字典，如果没有结果则返回None
        """
        for attempt in range(self.max_retries):
            try:
                self.ensure_connection()
                if self.connection is None:
                    log.error("无法执行查询，MySQL连接失败")
                    return None
                
                with self.connection.cursor() as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchone()
            except pymysql.OperationalError as e:
                if attempt < self.max_retries - 1:
                    log.warning(f"MySQL操作错误，尝试重新连接: {e}")
                    try:
                        self.connection.close()
                    except:
                        pass
                    self.connection = None
                    time.sleep(self.retry_delay)
                else:
                    log.error(f"MySQL查询失败，已达到最大重试次数: {e}")
                    raise
            except Exception as e:
                log.error(f"MySQL查询执行失败: {e}")
                raise
        
        return None
    
    def fetch_all(self, query: str, params: tuple = None) -> List[Dict]:
        """
        执行查询并返回所有结果
        
        参数:
            query: SQL查询语句
            params: 查询参数
            
        返回:
            results: 查询结果列表
        """
        for attempt in range(self.max_retries):
            try:
                self.ensure_connection()
                if self.connection is None:
                    log.error("无法执行查询，MySQL连接失败")
                    return []
                
                with self.connection.cursor() as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchall()
            except pymysql.OperationalError as e:
                if attempt < self.max_retries - 1:
                    log.warning(f"MySQL操作错误，尝试重新连接: {e}")
                    try:
                        self.connection.close()
                    except:
                        pass
                    self.connection = None
                    time.sleep(self.retry_delay)
                else:
                    log.error(f"MySQL查询失败，已达到最大重试次数: {e}")
                    raise
            except Exception as e:
                log.error(f"MySQL查询执行失败: {e}")
                raise
        
        return []
    
    def close(self):
        """关闭MySQL连接"""
        if self.connection:
            try:
                self.connection.close()
                log.info("MySQL连接已关闭")
            except Exception as e:
                log.error(f"关闭MySQL连接失败: {e}")
            finally:
                self.connection = None
    
    def __del__(self):
        """析构函数，确保连接被关闭"""
        self.close()


# 创建MySQL管理器单例
mysql_manager = MySQLManager() 