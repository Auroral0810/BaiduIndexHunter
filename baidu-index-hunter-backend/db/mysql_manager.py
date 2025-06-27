"""
MySQL数据库管理模块
"""
import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from datetime import datetime, timedelta
from utils.logger import log
from config.settings import MYSQL_CONFIG
import mysql.connector


class MySQLManager:
    """MySQL数据库管理器，处理cookie相关的数据库操作"""
    def __init__(self):
        self.db_config = MYSQL_CONFIG
        self.conn = None
    
    def connect(self):
        """连接数据库"""
        try:
            self.conn = mysql.connector.connect(**self.db_config)
            log.info(f"成功连接到MySQL数据库: {self.db_config['host']}:{self.db_config['port']}")
            return True
        except Exception as e:
            log.error(f"MySQL连接失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            log.debug("MySQL连接已关闭")
    
    def get_cursor(self):
        """
        获取数据库游标
        :return: 数据库游标上下文管理器
        """
        try:
            if self.conn is None or not self.conn.is_connected():
                self.conn = mysql.connector.connect(**self.db_config)
                log.info("已建立MySQL连接")
            
            cursor = self.conn.cursor(dictionary=True, buffered=True)
            
            # 自定义上下文管理器
            class CursorContextManager:
                def __init__(self, cursor, connection):
                    self.cursor = cursor
                    self.connection = connection
                
                def __enter__(self):
                    return self.cursor
                
                def __exit__(self, exc_type, exc_val, exc_tb):
                    if exc_type is None:
                        # 如果没有异常，提交事务
                        self.connection.commit()
                    else:
                        # 如果有异常，回滚事务
                        self.connection.rollback()
                        log.error(f"数据库操作失败: {exc_val}")
                    self.cursor.close()
                    return False  # 不吞噬异常
            
            return CursorContextManager(cursor, self.conn)
        
        except Exception as e:
            log.error(f"获取数据库游标失败: {e}")
            raise
    
    def get_all_cookies(self):
        """获取所有的cookie记录"""
        with self.get_cursor() as cursor:
            sql = "SELECT * FROM cookies"
            cursor.execute(sql)
            return cursor.fetchall()
    
    def get_available_cookies(self):
        """获取所有可用的cookie记录"""
        with self.get_cursor() as cursor:
            sql = "SELECT * FROM cookies WHERE is_available = TRUE"
            cursor.execute(sql)
            cookies = cursor.fetchall()
            # 添加兼容字段，将is_available=1的cookie视为未锁定
            for cookie in cookies:
                cookie['is_locked'] = False
                cookie['lock_time'] = None
            return cookies
    
    def get_cookies_by_account_id(self, account_id=None):
        """
        获取指定account_id的所有cookie记录，如果不指定则获取所有可用账号的cookie
        :param account_id: 账号ID，如果为None则获取所有可用账号
        :return: 按account_id分组的cookie字典
        """
        with self.get_cursor() as cursor:
            if account_id:
                sql = "SELECT * FROM cookies WHERE account_id = %s AND is_available = TRUE"
                cursor.execute(sql, (account_id,))
            else:
                sql = "SELECT * FROM cookies WHERE is_available = TRUE"
                cursor.execute(sql)
            
            cookies = cursor.fetchall()
            
            # 按account_id分组
            grouped_cookies = {}
            for cookie in cookies:
                account_id = cookie['account_id']
                if account_id not in grouped_cookies:
                    grouped_cookies[account_id] = []
                grouped_cookies[account_id].append(cookie)
            
            return grouped_cookies
    
    def get_assembled_cookies(self):
        """
        获取所有可用账号的完整cookie字典
        :return: 完整的cookie字典列表，每个字典代表一个账号的完整cookie
        """
        grouped_cookies = self.get_cookies_by_account_id()
        assembled_cookies = []
        
        for account_id, cookies in grouped_cookies.items():
            cookie_dict = {}
            for cookie in cookies:
                cookie_dict[cookie['cookie_name']] = cookie['cookie_value']
            
            if cookie_dict:  # 只添加非空的cookie字典
                assembled_cookies.append({
                    'account_id': account_id,
                    'cookie_dict': cookie_dict
                })
        
        log.info(f"从数据库获取并组装了 {len(assembled_cookies)} 个完整cookie")
        return assembled_cookies
    
    def update_cookie_status(self, account_id, is_available, permanent=False):
        """
        更新Cookie的可用状态
        :param account_id: 账号ID
        :param is_available: 是否可用
        :param permanent: 是否永久封禁，如果为True且is_available为False，则设置last_updated为9999年
        :return: 是否更新成功
        """
        try:
            with self.get_cursor() as cursor:
                # 将布尔值转换为整数
                status_int = 1 if is_available else 0
                
                if not is_available and permanent:
                    # 永久封禁，设置last_updated为9999年
                    cursor.execute("""
                        UPDATE cookies 
                        SET is_available = %s, last_updated = '9999-12-31 23:59:59' 
                        WHERE account_id = %s
                    """, (status_int, account_id))
                    log.info(f"账号 {account_id} 的Cookie被永久封禁")
                else:
                    # 普通更新
                    cursor.execute("""
                        UPDATE cookies 
                        SET is_available = %s, last_updated = NOW() 
                        WHERE account_id = %s
                    """, (status_int, account_id))
                
                affected_rows = cursor.rowcount
                log.info(f"更新账号 {account_id} 的Cookie状态为 {'可用' if is_available else '锁定'}，影响 {affected_rows} 行")
                return affected_rows > 0
        except Exception as e:
            log.error(f"更新Cookie状态失败: {e}")
            return False
    
    
    def get_cookie_status(self, account_id):
        """
        获取指定账号ID的Cookie状态
        :param account_id: 账号ID
        :return: (is_available, last_updated) 元组，如果查询失败则返回 (None, None)
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT is_available, last_updated 
                    FROM cookies 
                    WHERE account_id = %s
                """, (account_id,))
                result = cursor.fetchone()
                
                if result:
                    return result['is_available'] == 1, result['last_updated']
                return None, None
        except Exception as e:
            log.error(f"获取Cookie状态失败: {e}")
            return None, None
    
    def update_cookie_lock_status(self, cookie_id, is_locked):
        """更新cookie的锁定状态（兼容方法，实际上更新is_available）"""
        # 在我们的数据库中，is_locked对应的是is_available的反向值
        is_available = not is_locked
        lock_time = datetime.now() if is_locked else None
        log_msg = "锁定" if is_locked else "解锁"
        
        with self.get_cursor() as cursor:
            sql = "UPDATE cookies SET is_available = %s, last_updated = %s WHERE id = %s"
            cursor.execute(sql, (is_available, datetime.now(), cookie_id))
            log.info(f"Cookie {cookie_id} 已{log_msg}")
            return cursor.rowcount
    
    def update_cookie_value(self, cookie_id, cookie_value, expire_time=None):
        """更新cookie的值和过期时间"""
        with self.get_cursor() as cursor:
            if expire_time:
                sql = "UPDATE cookies SET cookie_value = %s, expire_time = %s, is_available = TRUE WHERE id = %s"
                cursor.execute(sql, (cookie_value, expire_time, cookie_id))
            else:
                sql = "UPDATE cookies SET cookie_value = %s, is_available = TRUE WHERE id = %s"
                cursor.execute(sql, (cookie_value, cookie_id))
            return cursor.rowcount
    
    def get_cookie_by_account(self, account_id):
        """根据账号ID获取cookie信息"""
        with self.get_cursor() as cursor:
            sql = "SELECT * FROM cookies WHERE account_id = %s"
            cursor.execute(sql, (account_id,))
            return cursor.fetchone()
    
    def get_expired_cookies(self, buffer_seconds=0):
        """获取已过期或即将过期的cookie记录"""
        expire_time = datetime.now() + timedelta(seconds=buffer_seconds)
        with self.get_cursor() as cursor:
            sql = """
                SELECT * FROM cookies 
                WHERE is_available = TRUE 
                AND (expire_time IS NULL OR expire_time <= %s)
            """
            cursor.execute(sql, (expire_time,))
            return cursor.fetchall()
    
    def add_new_cookie(self, account_id, cookie_name, cookie_value, expire_time=None):
        """添加新的cookie记录"""
        with self.get_cursor() as cursor:
            sql = """
                INSERT INTO cookies (account_id, cookie_name, cookie_value, expire_time) 
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (account_id, cookie_name, cookie_value, expire_time))
            return cursor.lastrowid
    
    def get_all_valid_cookies(self):
        """
        获取所有有效的Cookie，并按账号ID分组
        :return: {account_id: cookie_dict} 格式的字典
        """
        result = {}
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT account_id, cookie_name, cookie_value 
                    FROM cookies 
                    WHERE is_available = 1
                """)
                cookies = cursor.fetchall()
                
                # 按账号ID分组
                cookie_groups = {}
                for cookie in cookies:
                    account_id = cookie['account_id']
                    cookie_key = cookie['cookie_name']
                    cookie_value = cookie['cookie_value']
                    
                    if account_id not in cookie_groups:
                        cookie_groups[account_id] = {}
                    
                    cookie_groups[account_id][cookie_key] = cookie_value
                
                # 计算有效cookie数量
                valid_cookies_count = len(cookie_groups)
                log.info(f"从数据库获取并组装了 {valid_cookies_count} 个有效Cookie")
                
                return cookie_groups
        except Exception as e:
            log.error(f"从MySQL获取Cookie失败: {e}")
            return {}


# 创建数据库管理器单例
mysql_manager = MySQLManager() 