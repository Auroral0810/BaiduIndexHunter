"""
Cookie管理器 - 提供对数据库中cookie的CRUD操作
"""
import json
import time
import pymysql
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path

# 添加项目根目录到路径

# 添加项目根目录到路径，以便导入项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import MYSQL_CONFIG

class CookieManager:
    """Cookie管理器，负责cookie的增删改查和状态管理"""
    
    def __init__(self):
        """初始化数据库连接"""
        self.conn = pymysql.connect(
            host=MYSQL_CONFIG['host'],
            port=MYSQL_CONFIG['port'],
            user=MYSQL_CONFIG['user'],
            password=MYSQL_CONFIG['password'],
            db=MYSQL_CONFIG['db'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    
    def _get_cursor(self):
        """获取数据库游标"""
        if self.conn.open is False:
            self.conn = pymysql.connect(
                host=MYSQL_CONFIG['host'],
                port=MYSQL_CONFIG['port'],
                user=MYSQL_CONFIG['user'],
                password=MYSQL_CONFIG['password'],
                db=MYSQL_CONFIG['db'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
        return self.conn.cursor()
    
    def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'conn') and self.conn.open:
            self.conn.close()
    
    def parse_cookie_string(self, cookie_string):
        """
        解析完整的cookie字符串为字典
        
        Args:
            cookie_string: 完整的cookie字符串，如"name1=value1; name2=value2"
            
        Returns:
            解析后的cookie字典
        """
        cookies = {}
        if not cookie_string:
            return cookies
            
        items = cookie_string.split(';')
        for item in items:
            if '=' not in item:
                continue
            name, value = item.strip().split('=', 1)
            cookies[name] = value
        return cookies
    
    def add_cookie(self, account_id, cookie_data, expire_time=None):
        """
        添加cookie到数据库
        
        Args:
            account_id: 账号ID
            cookie_data: cookie数据，可以是字典、字符串或JSON格式
            expire_time: 过期时间，默认为None
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            cursor = self._get_cursor()
            
            # 处理cookie数据
            if isinstance(cookie_data, str):
                # 尝试解析为JSON
                try:
                    cookie_dict = json.loads(cookie_data)
                except:
                    # 尝试解析为cookie字符串
                    cookie_dict = self.parse_cookie_string(cookie_data)
            elif isinstance(cookie_data, dict):
                cookie_dict = cookie_data
            else:
                return False
            
            # 构建过期时间
            if expire_time is None:
                expire_time = datetime.now() + timedelta(days=365)  # 默认一年后过期
            
            # 插入每个cookie
            for name, value in cookie_dict.items():
                sql = """
                INSERT INTO cookies (account_id, cookie_name, cookie_value, expire_time, is_available)
                VALUES (%s, %s, %s, %s, 1)
                ON DUPLICATE KEY UPDATE 
                cookie_value = %s, expire_time = %s, is_available = 1
                """
                cursor.execute(sql, (account_id, name, value, expire_time, value, expire_time))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"添加cookie失败: {e}")
            self.conn.rollback()
            return False
    
    def delete_by_account_id(self, account_id):
        """
        根据账号ID删除所有相关cookie
        
        Args:
            account_id: 账号ID
            
        Returns:
            删除的记录数
        """
        try:
            cursor = self._get_cursor()
            sql = "DELETE FROM cookies WHERE account_id = %s"
            cursor.execute(sql, (account_id,))
            deleted_count = cursor.rowcount
            self.conn.commit()
            return deleted_count
        except Exception as e:
            print(f"删除cookie失败: {e}")
            self.conn.rollback()
            return 0
    
    def update_cookie(self, cookie_id, update_data):
        """
        更新cookie字段
        
        Args:
            cookie_id: cookie的ID
            update_data: 要更新的字段，字典格式
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            cursor = self._get_cursor()
            
            # 构建更新SQL
            set_clause = ", ".join([f"{k} = %s" for k in update_data.keys()])
            sql = f"UPDATE cookies SET {set_clause} WHERE id = %s"
            
            # 构建参数
            params = list(update_data.values())
            params.append(cookie_id)
            
            # 执行更新
            cursor.execute(sql, tuple(params))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"更新cookie失败: {e}")
            self.conn.rollback()
            return False
    
    def ban_account_permanently(self, account_id):
        """
        永久封禁指定账号ID的所有cookie
        
        Args:
            account_id: 账号ID
            
        Returns:
            成功返回被封禁的记录数，失败返回0
        """
        try:
            cursor = self._get_cursor()
            sql = "UPDATE cookies SET is_available = 0, is_permanently_banned = 1 WHERE account_id = %s"
            cursor.execute(sql, (account_id,))
            banned_count = cursor.rowcount
            self.conn.commit()
            return banned_count
        except Exception as e:
            print(f"永久封禁账号失败: {e}")
            self.conn.rollback()
            return 0
    
    def ban_account_temporarily(self, account_id, duration_seconds=1800):
        """
        暂时封禁指定账号ID的所有cookie
        
        Args:
            account_id: 账号ID
            duration_seconds: 封禁持续时间(秒)，默认30分钟
            
        Returns:
            成功返回被封禁的记录数，失败返回0
        """
        try:
            cursor = self._get_cursor()
            unban_time = datetime.now() + timedelta(seconds=duration_seconds)
            sql = """
            UPDATE cookies 
            SET is_available = 0, temp_ban_until = %s
            WHERE account_id = %s
            """
            cursor.execute(sql, (unban_time, account_id))
            banned_count = cursor.rowcount
            self.conn.commit()
            return banned_count
        except Exception as e:
            print(f"暂时封禁账号失败: {e}")
            self.conn.rollback()
            return 0
    
    def unban_account(self, account_id):
        """
        解封指定账号ID的所有cookie（只解封临时封禁的，永久封禁的不解封）
        
        Args:
            account_id: 账号ID
            
        Returns:
            成功返回解封的记录数，失败返回0
        """
        try:
            cursor = self._get_cursor()
            sql = """
            UPDATE cookies 
            SET is_available = 1, temp_ban_until = NULL
            WHERE account_id = %s AND is_permanently_banned = 0
            """
            cursor.execute(sql, (account_id,))
            unbanned_count = cursor.rowcount
            self.conn.commit()
            return unbanned_count
        except Exception as e:
            print(f"解封账号失败: {e}")
            self.conn.rollback()
            return 0
    
    def force_unban_account(self, account_id):
        """
        强制解封指定账号ID的所有cookie（包括永久封禁的）
        
        Args:
            account_id: 账号ID
            
        Returns:
            成功返回解封的记录数，失败返回0
        """
        try:
            cursor = self._get_cursor()
            sql = """
            UPDATE cookies 
            SET is_available = 1, is_permanently_banned = 0, temp_ban_until = NULL
            WHERE account_id = %s
            """
            cursor.execute(sql, (account_id,))
            unbanned_count = cursor.rowcount
            self.conn.commit()
            return unbanned_count
        except Exception as e:
            print(f"强制解封账号失败: {e}")
            self.conn.rollback()
            return 0
    
    
    
    def get_cookies_by_account_id(self, account_id):
        """
        获取指定账号ID的所有cookie
        
        Args:
            account_id: 账号ID
            
        Returns:
            cookie记录列表
        """
        try:
            cursor = self._get_cursor()
            sql = "SELECT * FROM cookies WHERE account_id = %s"
            cursor.execute(sql, (account_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"获取cookie失败: {e}")
            return []
    
    def get_available_cookies(self):
        """
        获取所有可用的cookie
        
        Returns:
            可用的cookie记录列表
        """
        try:
            cursor = self._get_cursor()
            sql = """
            SELECT * FROM cookies 
            WHERE is_available = 1 
            AND (expire_time IS NULL OR expire_time > NOW())
            AND (temp_ban_until IS NULL OR temp_ban_until < NOW())
            AND is_permanently_banned = 0
            """
            cursor.execute(sql)
            return cursor.fetchall()
        except Exception as e:
            print(f"获取可用cookie失败: {e}")
            return []
    
    def get_cookies_by_account_ids(self, account_ids=None):
        """
        按账号ID分组获取cookie
        
        Args:
            account_ids: 账号ID列表，如果为None则获取所有可用账号的cookie
            
        Returns:
            {account_id: [cookie1, cookie2, ...]} 格式的字典
        """
        try:
            cursor = self._get_cursor()
            
            if account_ids:
                # 获取指定账号的cookie
                placeholders = ','.join(['%s'] * len(account_ids))
                sql = f"""
                SELECT * FROM cookies 
                WHERE account_id IN ({placeholders})
                """
                cursor.execute(sql, tuple(account_ids))
            else:
                # 获取所有可用账号的cookie
                sql = """
                SELECT * FROM cookies 
                WHERE is_available = 1 
                AND (expire_time IS NULL OR expire_time > NOW())
                AND (temp_ban_until IS NULL OR temp_ban_until < NOW())
                AND is_permanently_banned = 0
                """
                cursor.execute(sql)
            
            cookies = cursor.fetchall()
            
            # 按账号ID分组
            grouped_cookies = {}
            for cookie in cookies:
                account_id = cookie['account_id']
                if account_id not in grouped_cookies:
                    grouped_cookies[account_id] = []
                grouped_cookies[account_id].append(cookie)
            
            return grouped_cookies
        except Exception as e:
            print(f"按账号ID获取cookie失败: {e}")
            return {}
    
    def get_assembled_cookies(self, account_ids=None):
        """
        获取所有可用账号的完整cookie字典
        
        Args:
            account_ids: 账号ID列表，如果为None则获取所有可用账号的cookie
            
        Returns:
            完整的cookie字典列表，每个字典代表一个账号的完整cookie
        """
        try:
            grouped_cookies = self.get_cookies_by_account_ids(account_ids)
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
            
            print(f"从数据库获取并组装了 {len(assembled_cookies)} 个完整cookie")
            return assembled_cookies
        except Exception as e:
            print(f"获取组装的cookie失败: {e}")
            return []
    
    def get_available_account_ids(self):
        """
        获取所有可用的账号ID列表
        
        Returns:
            可用的账号ID列表
        """
        try:
            cursor = self._get_cursor()
            sql = """
            SELECT DISTINCT account_id FROM cookies 
            WHERE is_available = 1 
            AND (expire_time IS NULL OR expire_time > NOW())
            AND (temp_ban_until IS NULL OR temp_ban_until < NOW())
            AND is_permanently_banned = 0
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            return [item['account_id'] for item in results]
        except Exception as e:
            print(f"获取可用账号ID失败: {e}")
            return []
    
    def update_account_id(self, old_account_id, new_account_id):
        """
        更新账号ID
        
        Args:
            old_account_id: 原账号ID
            new_account_id: 新账号ID
            
        Returns:
            更新的记录数
        """
        try:
            cursor = self._get_cursor()
            sql = "UPDATE cookies SET account_id = %s WHERE account_id = %s"
            cursor.execute(sql, (new_account_id, old_account_id))
            updated_count = cursor.rowcount
            self.conn.commit()
            return updated_count
        except Exception as e:
            print(f"更新账号ID失败: {e}")
            self.conn.rollback()
            return 0
    
    def check_and_update_cookie_status(self):
        """
        检查并更新cookie状态，将临时封禁过期的cookie恢复可用
        
        Returns:
            更新的记录数
        """
        try:
            cursor = self._get_cursor()
            sql = """
            UPDATE cookies 
            SET is_available = 1
            WHERE is_available = 0 
            AND is_permanently_banned = 0
            AND temp_ban_until IS NOT NULL 
            AND temp_ban_until < NOW()
            """
            cursor.execute(sql)
            updated_count = cursor.rowcount
            self.conn.commit()
            return updated_count
        except Exception as e:
            print(f"更新cookie状态失败: {e}")
            self.conn.rollback()
            return 0
    
    def cleanup_expired_cookies(self):
        """
        清理已过期的cookie
        
        Returns:
            删除的记录数
        """
        try:
            cursor = self._get_cursor()
            sql = """
            DELETE FROM cookies 
            WHERE expire_time IS NOT NULL AND expire_time < NOW()
            """
            cursor.execute(sql)
            deleted_count = cursor.rowcount
            self.conn.commit()
            return deleted_count
        except Exception as e:
            print(f"清理过期cookie失败: {e}")
            self.conn.rollback()
            return 0

    def __del__(self):
        """析构函数，确保连接被关闭"""
        self.close()
