"""
MySQL数据库连接管理模块
"""
import os
import sys
import time
import pymysql
from pymysql.cursors import DictCursor
from typing import List, Dict, Any, Optional, Union, Tuple

from src.core.logger import log
from src.core.config import MYSQL_CONFIG


import threading

class MySQLManager:
    """MySQL数据库连接管理器"""
    
    def __init__(self, config=None):
        """
        初始化MySQL连接管理器
        
        参数:
            config: MySQL配置，如果为None则使用settings.py中的配置
        """
        self.config = MYSQL_CONFIG
        self.max_retries = 3
        self.retry_delay = 2  # 秒
        
        # 使用thread-local存储每个线程的连接
        self.local = threading.local()
    
    def _connect(self):
        """建立MySQL连接"""
        try:
            connection = pymysql.connect(
                host=self.config['host'],
                port=self.config.get('port', 3306),
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['db'],
                charset=self.config.get('charset', 'utf8mb4'),
                cursorclass=DictCursor,
                autocommit=True
            )
            # log.info(f"MySQL连接成功: {self.config['host']}:{self.config.get('port', 3306)}/{self.config['db']}")
            return connection
        except Exception as e:
            log.error(f"MySQL连接失败: {e}")
            return None
    
    def _get_connection(self):
        """获取当前线程的MySQL连接"""
        if not hasattr(self.local, 'connection') or self.local.connection is None:
            self.local.connection = self._connect()
        else:
            try:
                # 检查连接是否有效
                self.local.connection.ping(reconnect=False)
            except:
                log.warning("MySQL连接已断开，尝试重新连接")
                try:
                    self.local.connection.close()
                except:
                    pass
                self.local.connection = self._connect()
        
        return self.local.connection

    def ensure_connection(self):
        """确保MySQL连接有效（为了兼容旧代码接口，实际逻辑已移至_get_connection）"""
        self._get_connection()
    
    @property
    def connection(self):
        """兼容旧代码的connection属性访问"""
        return self._get_connection()

    @connection.setter
    def connection(self, value):
        """兼容旧代码的connection属性设置"""
        self.local.connection = value
    
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
    def insert(self, table, data):
        """
        插入数据
        :param table: 表名
        :param data: 数据字典
        :return: 插入的ID
        """
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['%s'] * len(data))
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, list(data.values()))
                    conn.commit()
                    return cursor.lastrowid
        except Exception as e:
            log.error(f"插入数据失败: {e}")
            log.error(f"表: {table}")
            log.error(f"数据: {data}")
            raise
    
    def update(self, table, data, condition, condition_params=None):
        """
        更新数据
        :param table: 表名
        :param data: 要更新的数据字典
        :param condition: 条件语句
        :param condition_params: 条件参数
        :return: 影响的行数
        """
        try:
            set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
            query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
            
            params = list(data.values())
            if condition_params:
                if isinstance(condition_params, (list, tuple)):
                    params.extend(condition_params)
                else:
                    params.append(condition_params)
            
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.rowcount
        except Exception as e:
            log.error(f"更新数据失败: {e}")
            log.error(f"表: {table}")
            log.error(f"数据: {data}")
            log.error(f"条件: {condition}")
            raise
    
    def delete(self, table, condition, params=None):
        """
        删除数据
        :param table: 表名
        :param condition: 条件语句
        :param params: 条件参数
        :return: 影响的行数
        """
        try:
            query = f"DELETE FROM {table} WHERE {condition}"
            
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.rowcount
        except Exception as e:
            log.error(f"删除数据失败: {e}")
            log.error(f"表: {table}")
            log.error(f"条件: {condition}")
            raise
    
    def close(self):
        """关闭MySQL连接"""
        if self.connection:
            try:
                self.connection.close()
                # log.info("MySQL连接已关闭")
            except Exception as e:
                log.error(f"关闭MySQL连接失败: {e}")
            finally:
                self.connection = None
    
    def __del__(self):
        """析构函数，确保连接被关闭"""
        self.close()

# 创建MySQL管理器单例
mysql_manager = MySQLManager() 