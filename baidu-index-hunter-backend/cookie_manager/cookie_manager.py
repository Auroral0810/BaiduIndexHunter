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
import requests
from fake_useragent import UserAgent
from typing import Dict, List, Tuple, Any, Optional, Set, Union
import execjs
import redis
from utils.ab_sr_update import AbSrUpdater
from utils.logger import log
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目根目录到路径，以便导入项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import MYSQL_CONFIG, REDIS_CONFIG

class CookieManager:
    """Cookie管理器，负责cookie的增删改查和状态管理"""
    
    # Redis键名
    REDIS_COOKIES_KEY = "baidu_index:cookies"  # 所有cookie数据
    REDIS_COOKIE_COUNT_KEY = "baidu_index:cookie_count"  # cookie数量统计
    REDIS_COOKIE_STATUS_KEY = "baidu_index:cookie_status"  # cookie状态
    REDIS_COOKIE_BAN_KEY = "baidu_index:cookie_ban"  # cookie封禁信息
    
    # Redis过期时间（7天）
    REDIS_EXPIRE = 60 * 60 * 24 * 7
    
    def __init__(self):
        """初始化数据库连接"""
        self.conn = None
        self._connect_db()
        
        # 初始化Redis连接
        self.redis_client = None
        self._connect_redis()
    
    def _connect_db(self):
        """连接到MySQL数据库"""
        max_retries = 3
        retry_delay = 2  # 秒
        
        for attempt in range(max_retries):
            try:
                self.conn = pymysql.connect(
                    host=MYSQL_CONFIG['host'],
                    port=MYSQL_CONFIG['port'],
                    user=MYSQL_CONFIG['user'],
                    password=MYSQL_CONFIG['password'],
                    db=MYSQL_CONFIG['db'],
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor,
                    connect_timeout=10,  # 增加连接超时时间
                    read_timeout=30,     # 增加读取超时时间
                    write_timeout=30     # 增加写入超时时间
                )
                log.info("成功连接到MySQL数据库")
                return
            except Exception as e:
                log.error(f"连接MySQL数据库失败: {e}")
                if attempt < max_retries - 1:
                    log.info(f"尝试重新连接MySQL，第 {attempt + 1} 次...")
                    time.sleep(retry_delay)
                else:
                    log.error("已达到最大重试次数，无法连接到MySQL数据库")
                    self.conn = None
    
    def _connect_redis(self):
        """连接Redis"""
        try:
            self.redis_client = redis.Redis(
                host=REDIS_CONFIG['host'],
                port=REDIS_CONFIG['port'],
                db=REDIS_CONFIG['db'],
                password=REDIS_CONFIG['password'],
                decode_responses=True  # 自动将字节解码为字符串
            )
            log.info("成功连接到Redis")
        except Exception as e:
            log.error(f"连接Redis失败: {e}")
            self.redis_client = None
    
    def _get_cursor(self):
        """获取数据库游标，确保连接是活跃的"""
        max_retries = 3
        retry_delay = 1  # 秒
        
        for attempt in range(max_retries):
            try:
                # 如果连接不存在或已关闭，重新连接
                if self.conn is None or not self.conn.open:
                    self._connect_db()
                    if self.conn is None:
                        log.error("无法建立数据库连接")
                        if attempt < max_retries - 1:
                            log.info(f"尝试重新连接，第 {attempt + 1} 次...")
                            time.sleep(retry_delay)
                            continue
                        else:
                            raise Exception("无法建立数据库连接，已达到最大重试次数")
                
                # 尝试ping一下，确保连接活跃
                try:
                    self.conn.ping(reconnect=True)
                    return self.conn.cursor()
                except pymysql.Error as e:
                    log.warning(f"数据库连接已断开，尝试重新连接: {e}")
                    try:
                        self.conn.close()
                    except:
                        pass
                    self.conn = None
                    
                    if attempt < max_retries - 1:
                        log.info(f"尝试重新连接，第 {attempt + 1} 次...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise Exception(f"无法重新连接到数据库，已达到最大重试次数: {e}")
                    
            except Exception as e:
                log.error(f"获取数据库游标失败: {e}")
                
                # 尝试重新连接
                try:
                    if self.conn:
                        self.conn.close()
                except:
                    pass
                
                self.conn = None
                self._connect_db()
                
                if self.conn is None:
                    if attempt < max_retries - 1:
                        log.info(f"尝试重新连接，第 {attempt + 1} 次...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise Exception(f"无法重新连接到数据库，已达到最大重试次数: {e}")
        
        # 如果所有重试都失败了，但代码执行到这里（不应该发生），抛出异常
        raise Exception("无法获取数据库游标，所有重试均已失败")
    
    def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'conn') and self.conn and self.conn.open:
            self.conn.close()
            self.conn = None
        if self.redis_client:
            self.redis_client.close()
            self.redis_client = None
    
    def sync_to_redis(self):
        """将MySQL中的cookie数据同步到Redis"""
        try:
            log.info("开始同步cookie数据到Redis...")
            
            # 清除Redis中的旧数据
            self._clear_redis_cookies()
            
            # 获取所有可用且未被永久封禁的cookie
            cookies = self.get_available_cookies()
            
            # 按账号ID分组
            cookies_by_account = {}
            for cookie in cookies:
                account_id = cookie['account_id']
                if account_id not in cookies_by_account:
                    cookies_by_account[account_id] = []
                cookies_by_account[account_id].append(cookie)
            
            # 组装每个账号的cookie并存入Redis
            available_count = 0
            for account_id, account_cookies in cookies_by_account.items():
                # 组装cookie字典
                cookie_dict = {}
                is_available = True
                is_permanently_banned = False
                temp_ban_until = None
                
                for cookie in account_cookies:
                    cookie_dict[cookie['cookie_name']] = cookie['cookie_value']
                    
                    # 如果任一cookie不可用或被永久封禁，则整个账号被视为不可用
                    if not cookie['is_available']:
                        is_available = False
                    if cookie.get('is_permanently_banned'):
                        is_permanently_banned = True
                    
                    # 记录临时封禁时间（取最大值）
                    if cookie.get('temp_ban_until'):
                        if temp_ban_until is None or cookie['temp_ban_until'] > temp_ban_until:
                            temp_ban_until = cookie['temp_ban_until']
                
                # 将cookie数据存入Redis
                self._save_cookie_to_redis(account_id, cookie_dict, is_available, is_permanently_banned, temp_ban_until)
                
                if is_available and not is_permanently_banned and (temp_ban_until is None or temp_ban_until < datetime.now()):
                    available_count += 1
            
            # 更新可用cookie数量
            self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, available_count)
            self.redis_client.expire(self.REDIS_COOKIE_COUNT_KEY, self.REDIS_EXPIRE)
            
            log.info(f"成功同步 {len(cookies_by_account)} 个账号的cookie数据到Redis，其中 {available_count} 个可用")
            return True
        except Exception as e:
            log.error(f"同步cookie数据到Redis失败: {e}")
            return False
    
    def _clear_redis_cookies(self):
        """清空Redis中的cookie数据"""
        try:
            if not self.redis_client:
                self._connect_redis()
                if not self.redis_client:
                    return
            
            # 删除所有相关的键
            self.redis_client.delete(self.REDIS_COOKIES_KEY)
            self.redis_client.delete(self.REDIS_COOKIE_COUNT_KEY)
            self.redis_client.delete(self.REDIS_COOKIE_STATUS_KEY)
            self.redis_client.delete(self.REDIS_COOKIE_BAN_KEY)
            
            log.info("已清空Redis中的cookie数据")
        except Exception as e:
            log.error(f"清空Redis cookie数据失败: {e}")
    
    def _save_cookie_to_redis(self, account_id, cookie_dict, is_available, is_permanently_banned, temp_ban_until):
        """将cookie数据保存到Redis"""
        try:
            if not self.redis_client:
                self._connect_redis()
                if not self.redis_client:
                    return
            
            # 保存cookie数据
            cookie_data = {
                "account_id": account_id,
                "cookie": cookie_dict
            }
            self.redis_client.hset(self.REDIS_COOKIES_KEY, account_id, json.dumps(cookie_data, ensure_ascii=False))
            
            # 保存状态信息
            status_data = {
                "is_available": 1 if is_available else 0,
                "is_permanently_banned": 1 if is_permanently_banned else 0
            }
            self.redis_client.hset(self.REDIS_COOKIE_STATUS_KEY, account_id, json.dumps(status_data, ensure_ascii=False))
            
            # 保存封禁信息
            if temp_ban_until:
                ban_data = {
                    "temp_ban_until": temp_ban_until.strftime("%Y-%m-%d %H:%M:%S") if temp_ban_until else None
                }
                self.redis_client.hset(self.REDIS_COOKIE_BAN_KEY, account_id, json.dumps(ban_data, ensure_ascii=False))
            
            # 设置过期时间
            self.redis_client.expire(self.REDIS_COOKIES_KEY, self.REDIS_EXPIRE)
            self.redis_client.expire(self.REDIS_COOKIE_STATUS_KEY, self.REDIS_EXPIRE)
            self.redis_client.expire(self.REDIS_COOKIE_BAN_KEY, self.REDIS_EXPIRE)
        except Exception as e:
            log.error(f"保存cookie到Redis失败: {e}")
    
    def get_redis_cookie(self, account_id):
        """从Redis获取指定账号ID的cookie"""
        try:
            if not self.redis_client:
                self._connect_redis()
                if not self.redis_client:
                    return None
            
            # 获取cookie数据
            cookie_json = self.redis_client.hget(self.REDIS_COOKIES_KEY, account_id)
            if not cookie_json:
                return None
            
            cookie_data = json.loads(cookie_json)
            return cookie_data.get("cookie")
        except Exception as e:
            log.error(f"从Redis获取cookie失败: {e}")
            return None
    
    def get_redis_cookie_status(self, account_id):
        """从Redis获取指定账号ID的cookie状态"""
        try:
            if not self.redis_client:
                self._connect_redis()
                if not self.redis_client:
                    return None
            
            # 获取状态数据
            status_json = self.redis_client.hget(self.REDIS_COOKIE_STATUS_KEY, account_id)
            if not status_json:
                return None
            
            return json.loads(status_json)
        except Exception as e:
            log.error(f"从Redis获取cookie状态失败: {e}")
            return None
    
    def get_redis_cookie_ban_info(self, account_id):
        """从Redis获取指定账号ID的cookie封禁信息"""
        try:
            if not self.redis_client:
                self._connect_redis()
                if not self.redis_client:
                    return None
            
            # 获取封禁数据
            ban_json = self.redis_client.hget(self.REDIS_COOKIE_BAN_KEY, account_id)
            if not ban_json:
                return None
            
            return json.loads(ban_json)
        except Exception as e:
            log.error(f"从Redis获取cookie封禁信息失败: {e}")
            return None
    
    def get_redis_available_cookie_count(self):
        """从Redis获取可用cookie数量"""
        try:
            if not self.redis_client:
                self._connect_redis()
                if not self.redis_client:
                    return 0
            
            count = self.redis_client.get(self.REDIS_COOKIE_COUNT_KEY)
            return int(count) if count else 0
        except Exception as e:
            log.error(f"从Redis获取可用cookie数量失败: {e}")
            return 0
    
    def get_all_redis_cookies(self):
        """从Redis获取所有cookie数据"""
        try:
            if not self.redis_client:
                self._connect_redis()
                if not self.redis_client:
                    return {}
            
            # 获取所有cookie数据
            all_cookies = self.redis_client.hgetall(self.REDIS_COOKIES_KEY)
            result = {}
            
            for account_id, cookie_json in all_cookies.items():
                cookie_data = json.loads(cookie_json)
                result[account_id] = cookie_data.get("cookie")
            
            return result
        except Exception as e:
            log.error(f"从Redis获取所有cookie失败: {e}")
            return {}
    
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
            
            # 更新Redis中的数据
            if self.redis_client:
                # 获取更新后的cookie数据
                cookies = self.get_cookies_by_account_id(account_id)
                if cookies:
                    # 组装cookie字典
                    cookie_dict = {}
                    for cookie in cookies:
                        cookie_dict[cookie['cookie_name']] = cookie['cookie_value']
                    
                    # 更新Redis
                    self._save_cookie_to_redis(account_id, cookie_dict, True, False, None)
                    
                    # 更新可用cookie数量
                    available_count = self.get_redis_available_cookie_count()
                    self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, available_count + 1)
            
            return True
        except Exception as e:
            log.error(f"添加cookie失败: {e}")
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
            
            # 从Redis中删除相关数据
            if deleted_count > 0 and self.redis_client:
                # 检查是否是可用的cookie
                status_json = self.redis_client.hget(self.REDIS_COOKIE_STATUS_KEY, account_id)
                if status_json:
                    status = json.loads(status_json)
                    is_available = status.get("is_available") == 1
                    
                    # 如果是可用的cookie，更新计数
                    if is_available:
                        available_count = self.get_redis_available_cookie_count()
                        if available_count > 0:
                            self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, available_count - 1)
                
                # 删除Redis中的所有相关数据
                self.redis_client.hdel(self.REDIS_COOKIES_KEY, account_id)
                self.redis_client.hdel(self.REDIS_COOKIE_STATUS_KEY, account_id)
                self.redis_client.hdel(self.REDIS_COOKIE_BAN_KEY, account_id)
                
                log.info(f"已从Redis中删除账号 {account_id} 的所有数据")
            
            return deleted_count
        except Exception as e:
            log.error(f"删除cookie失败: {e}")
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
            # 先获取当前cookie的信息，包括account_id
            cursor = self._get_cursor()
            cursor.execute("SELECT * FROM cookies WHERE id = %s", (cookie_id,))
            current_cookie = cursor.fetchone()
            
            if not current_cookie:
                return False
            
            account_id = current_cookie['account_id']
            
            # 构建更新SQL
            set_clause = ", ".join([f"{k} = %s" for k in update_data.keys()])
            sql = f"UPDATE cookies SET {set_clause} WHERE id = %s"
            
            # 构建参数
            params = list(update_data.values())
            params.append(cookie_id)
            
            # 执行更新
            cursor.execute(sql, tuple(params))
            self.conn.commit()
            
            # 如果更新成功，同步到Redis
            if cursor.rowcount > 0 and self.redis_client:
                # 获取更新后的account的所有cookie
                cookies = self.get_cookies_by_account_id(account_id)
                if cookies:
                    # 检查是否有状态变更
                    status_changed = False
                    ban_changed = False
                    
                    for key in update_data:
                        if key in ('is_available', 'is_permanently_banned'):
                            status_changed = True
                        if key == 'temp_ban_until':
                            ban_changed = True
                    
                    # 组装cookie字典和状态
                    cookie_dict = {}
                    is_available = True
                    is_permanently_banned = False
                    temp_ban_until = None
                    
                    for cookie in cookies:
                        cookie_dict[cookie['cookie_name']] = cookie['cookie_value']
                        
                        # 如果任一cookie不可用或被永久封禁，则整个账号被视为不可用
                        if not cookie['is_available']:
                            is_available = False
                        if cookie.get('is_permanently_banned'):
                            is_permanently_banned = True
                        
                        # 记录临时封禁时间（取最大值）
                        if cookie.get('temp_ban_until'):
                            if temp_ban_until is None or cookie['temp_ban_until'] > temp_ban_until:
                                temp_ban_until = cookie['temp_ban_until']
                    
                    # 更新Redis
                    if is_permanently_banned:
                        # 永久封禁从Redis中删除
                        self.redis_client.hdel(self.REDIS_COOKIES_KEY, account_id)
                        self.redis_client.hdel(self.REDIS_COOKIE_STATUS_KEY, account_id)
                        self.redis_client.hdel(self.REDIS_COOKIE_BAN_KEY, account_id)
                    else:
                        # 更新Redis中的数据
                        self._save_cookie_to_redis(account_id, cookie_dict, is_available, False, temp_ban_until)
                    
                    # 更新计数
                    available_count = 0
                    # 获取所有账号
                    all_accounts = self.redis_client.hgetall(self.REDIS_COOKIE_STATUS_KEY)
                    for acc_id, status_json in all_accounts.items():
                        status = json.loads(status_json)
                        if status.get("is_available") == 1 and status.get("is_permanently_banned") == 0:
                            # 检查是否有临时封禁
                            ban_json = self.redis_client.hget(self.REDIS_COOKIE_BAN_KEY, acc_id)
                            if ban_json:
                                ban_data = json.loads(ban_json)
                                ban_until_str = ban_data.get("temp_ban_until")
                                if ban_until_str:
                                    ban_until = datetime.strptime(ban_until_str, "%Y-%m-%d %H:%M:%S")
                                    if ban_until > datetime.now():
                                        continue  # 跳过当前仍在封禁中的账号
                            
                            available_count += 1
                    
                    self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, available_count)
                    
                    log.info(f"已更新Redis中账号 {account_id} 的cookie数据")
            
            return cursor.rowcount > 0
        except Exception as e:
            log.error(f"更新cookie失败: {e}")
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
            
            # 更新Redis中的数据 - 永久封禁直接从Redis中删除
            if banned_count > 0 and self.redis_client:
                self.redis_client.hdel(self.REDIS_COOKIES_KEY, account_id)
                self.redis_client.hdel(self.REDIS_COOKIE_STATUS_KEY, account_id)
                self.redis_client.hdel(self.REDIS_COOKIE_BAN_KEY, account_id)
                
                # 更新计数
                available_count = self.get_redis_available_cookie_count()
                if available_count > 0:
                    self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, available_count - 1)
                
                log.info(f"已从Redis中删除永久封禁的账号 {account_id} 数据")
            
            return banned_count
        except Exception as e:
            log.error(f"永久封禁账号失败: {e}")
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
            
            # 更新Redis中的数据
            if banned_count > 0 and self.redis_client:
                # 更新状态信息
                status_data = {
                    "is_available": 0,
                    "is_permanently_banned": 0
                }
                self.redis_client.hset(self.REDIS_COOKIE_STATUS_KEY, account_id, json.dumps(status_data, ensure_ascii=False))
                
                # 更新封禁信息
                ban_data = {
                    "temp_ban_until": unban_time.strftime("%Y-%m-%d %H:%M:%S")
                }
                self.redis_client.hset(self.REDIS_COOKIE_BAN_KEY, account_id, json.dumps(ban_data, ensure_ascii=False))
                
                # 更新计数
                available_count = self.get_redis_available_cookie_count()
                if available_count > 0:
                    self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, available_count - 1)
                
                log.info(f"已更新Redis中临时封禁的账号 {account_id} 数据，封禁至 {unban_time}")
            
            return banned_count
        except Exception as e:
            log.error(f"暂时封禁账号失败: {e}")
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
            
            # 更新Redis中的数据
            if unbanned_count > 0 and self.redis_client:
                # 获取更新后的cookie数据
                cookies = self.get_cookies_by_account_id(account_id)
                if cookies:
                    # 组装cookie字典
                    cookie_dict = {}
                    for cookie in cookies:
                        cookie_dict[cookie['cookie_name']] = cookie['cookie_value']
                    
                    # 更新Redis中的cookie状态
                    status_data = {
                        "is_available": 1,
                        "is_permanently_banned": 0
                    }
                    self.redis_client.hset(self.REDIS_COOKIE_STATUS_KEY, account_id, json.dumps(status_data, ensure_ascii=False))
                    
                    # 删除封禁信息
                    self.redis_client.hdel(self.REDIS_COOKIE_BAN_KEY, account_id)
                    
                    # 更新cookie数据
                    cookie_data = {
                        "account_id": account_id,
                        "cookie": cookie_dict
                    }
                    self.redis_client.hset(self.REDIS_COOKIES_KEY, account_id, json.dumps(cookie_data, ensure_ascii=False))
                    
                    # 更新计数
                    available_count = self.get_redis_available_cookie_count()
                    self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, available_count + 1)
                    
                    log.info(f"已更新Redis中解封的账号 {account_id} 数据")
                
            return unbanned_count
        except Exception as e:
            log.error(f"解封账号失败: {e}")
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
            
            # 更新Redis中的数据
            if unbanned_count > 0 and self.redis_client:
                # 获取更新后的cookie数据
                cookies = self.get_cookies_by_account_id(account_id)
                if cookies:
                    # 组装cookie字典
                    cookie_dict = {}
                    for cookie in cookies:
                        cookie_dict[cookie['cookie_name']] = cookie['cookie_value']
                    
                    # 更新Redis
                    self._save_cookie_to_redis(account_id, cookie_dict, True, False, None)
                    
                    # 更新计数
                    available_count = self.get_redis_available_cookie_count()
                    self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, available_count + 1)
                    
                    log.info(f"已更新Redis中强制解封的账号 {account_id} 数据")
                
            return unbanned_count
        except Exception as e:
            log.error(f"强制解封账号失败: {e}")
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
            log.error(f"获取cookie失败: {e}")
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
            log.error(f"获取可用cookie失败: {e}")
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
            log.error(f"按账号ID获取cookie失败: {e}")
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
            
            log.info(f"从数据库获取并组装了 {len(assembled_cookies)} 个完整cookie")
            return assembled_cookies
        except Exception as e:
            log.error(f"获取组装的cookie失败: {e}")
            return []
    
    def get_available_account_ids(self):
        """
        获取所有可用的账号ID列表
        
        Returns:
            可用的账号ID列表
        """
        max_retries = 3
        retry_delay = 1  # 秒
        
        for attempt in range(max_retries):
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
            except pymysql.Error as e:
                log.error(f"获取可用账号ID失败: {e}")
                
                if attempt < max_retries - 1:
                    log.info(f"尝试重新获取可用账号ID，第 {attempt + 1} 次...")
                    time.sleep(retry_delay)
                    # 重新连接数据库
                    try:
                        if self.conn:
                            self.conn.close()
                    except:
                        pass
                    self.conn = None
                    self._connect_db()
                else:
                    log.error("获取可用账号ID失败，已达到最大重试次数")
                    return []
            except Exception as e:
                log.error(f"获取可用账号ID失败: {e}")
                return []
        
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
            # 先检查Redis中是否存在旧账号ID的数据
            redis_has_old_account = False
            if self.redis_client:
                redis_has_old_account = self.redis_client.hexists(self.REDIS_COOKIES_KEY, old_account_id)
            
            cursor = self._get_cursor()
            sql = "UPDATE cookies SET account_id = %s WHERE account_id = %s"
            cursor.execute(sql, (new_account_id, old_account_id))
            updated_count = cursor.rowcount
            self.conn.commit()
            
            # 如果Redis中存在旧账号ID的数据，需要更新
            if updated_count > 0 and redis_has_old_account and self.redis_client:
                # 获取旧账号的Redis数据
                cookie_json = self.redis_client.hget(self.REDIS_COOKIES_KEY, old_account_id)
                status_json = self.redis_client.hget(self.REDIS_COOKIE_STATUS_KEY, old_account_id)
                ban_json = self.redis_client.hget(self.REDIS_COOKIE_BAN_KEY, old_account_id)
                
                # 更新account_id并保存到新的键
                if cookie_json:
                    cookie_data = json.loads(cookie_json)
                    cookie_data["account_id"] = new_account_id
                    self.redis_client.hset(self.REDIS_COOKIES_KEY, new_account_id, json.dumps(cookie_data, ensure_ascii=False))
                
                if status_json:
                    self.redis_client.hset(self.REDIS_COOKIE_STATUS_KEY, new_account_id, status_json)
                
                if ban_json:
                    self.redis_client.hset(self.REDIS_COOKIE_BAN_KEY, new_account_id, ban_json)
                
                # 删除旧的键
                self.redis_client.hdel(self.REDIS_COOKIES_KEY, old_account_id)
                self.redis_client.hdel(self.REDIS_COOKIE_STATUS_KEY, old_account_id)
                self.redis_client.hdel(self.REDIS_COOKIE_BAN_KEY, old_account_id)
                
                log.info(f"已将Redis中账号 {old_account_id} 的数据更新为 {new_account_id}")
            
            return updated_count
        except Exception as e:
            log.error(f"更新账号ID失败: {e}")
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
            log.error(f"更新cookie状态失败: {e}")
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
            log.error(f"清理过期cookie失败: {e}")
            self.conn.rollback()
            return 0

    def test_cookies_availability(self) -> Dict[str, Any]:
        """测试所有可用Cookie的可用性
        
        测试条件：
        - 状态为0表示cookie有效可用
        - 状态为10000表示账号未登录，需要将该账号的所有cookie永久锁定
        - 状态为10001表示账号被锁定，需要将对应记录在MySQL中临时锁定30分钟
        - 状态为10002表示请求错误，不需要任何操作，但仍视为有效cookie
        
        Returns:
            Dict[str, Any]: 包含有效账号ID列表和总数的字典
        """
        log.info("开始测试Cookie可用性")
        
        # 获取所有可用的账号ID
        account_ids = self.get_available_account_ids()
        log.info(f"获取到 {len(account_ids)} 个可用账号")
        
        valid_accounts = []
        banned_accounts = []
        not_login_accounts = []
        
        # 创建线程锁，保护共享变量
        valid_lock = threading.Lock()
        banned_lock = threading.Lock()
        not_login_lock = threading.Lock()
        conn_lock = threading.Lock()  # 添加数据库连接锁
        
        # 定义单个账号测试函数
        def test_single_account(account_id):
            # 为每个线程创建独立的数据库连接
            local_conn = None
            try:
                # 获取账号的cookie
                with conn_lock:
                    cookies = self.get_cookie_by_account_id(account_id)
                
                if not cookies:
                    log.warning(f"账号 {account_id} 没有可用的cookie")
                    with not_login_lock:
                        not_login_accounts.append(account_id)
                    
                    # 永久封禁并从Redis中删除
                    try:
                        with conn_lock:
                            self.ban_account_permanently(account_id)
                    except Exception as e:
                        log.error(f"永久封禁账号 {account_id} 时发生错误: {str(e)}")
                    
                    return
                
                # 测试参数
                city_number = "911"  # 北京
                word = "电脑"
                # 计算日期范围（最近30天）
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                startDate = start_date.strftime("%Y-%m-%d")
                endDate = end_date.strftime("%Y-%m-%d")
                
                # 创建UserAgent实例
                ua = UserAgent()
                
                # 组装cookie字符串
                cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
                url_cipyter = f'https://index.baidu.com/v2/main/index.html#/trend/{word}?words={word}'
            
                # 获取cipher-text
                try:
                    with open('/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/utils/Cipher-Text.js', 'r') as f:
                        js = f.read()
                        ctx = execjs.compile(js)
                    cipyer_text = ctx.call('ascToken', url_cipyter, ua.random)
                except Exception as e:
                    log.error(f"生成cipher-text失败: {e}")
                    cipyer_text = ""
            
                headers = {
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Cache-Control': 'no-cache',
                    'Cipher-Text': cipyer_text,
                    'Connection': 'keep-alive',
                    'Pragma': 'no-cache',
                    'Referer': 'https://index.baidu.com/v2/main/index.html',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'User-Agent': ua.random,
                    'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"macOS"',
                    "Cookie": cookie_str
                }
                
                # 构建请求URL
                url = f'https://index.baidu.com/api/SearchApi/index?area={city_number}&word=[[{{"name":"{word}","wordType":1}}]]&startDate={startDate}&endDate={endDate}'
                
                # 发送请求
                response = requests.get(url, headers=headers, timeout=10)
                data = response.json()
                
                # 检查响应状态
                status = data.get("status", -1)
                message = data.get("message", "")
                
                log.debug(f"账号 {account_id} 测试结果: status={status}, message={message}")
                
                if status == 0:
                    # 状态为0表示cookie有效可用
                    log.info(f"账号 {account_id} 的cookie有效可用")
                    with valid_lock:
                        valid_accounts.append(account_id)
                    
                    # 确保Redis状态正确
                    if self.redis_client:
                        with conn_lock:
                            cookies = self.get_cookies_by_account_id(account_id)
                        if cookies:
                            # 组装cookie字典
                            cookie_dict = {}
                            for cookie in cookies:
                                cookie_dict[cookie['cookie_name']] = cookie['cookie_value']
                            
                            # 更新Redis中的状态
                            self._save_cookie_to_redis(account_id, cookie_dict, True, False, None)
                    
                elif status == 10000:
                    # 状态为10000表示账号未登录，需要将该账号的所有cookie永久锁定
                    log.warning(f"账号 {account_id} 未登录，将被永久锁定")
                    try:
                        with conn_lock:
                            self.ban_account_permanently(account_id)
                    except Exception as e:
                        log.error(f"永久封禁账号 {account_id} 时发生错误: {str(e)}")
                    with not_login_lock:
                        not_login_accounts.append(account_id)
                    
                    # Redis中直接删除该账号数据
                    if self.redis_client:
                        self.redis_client.hdel(self.REDIS_COOKIES_KEY, account_id)
                        self.redis_client.hdel(self.REDIS_COOKIE_STATUS_KEY, account_id)
                        self.redis_client.hdel(self.REDIS_COOKIE_BAN_KEY, account_id)
                    
                elif status == 10001:
                    # 状态为10001表示账号被锁定，需要将对应记录在MySQL中临时锁定30分钟
                    log.warning(f"账号 {account_id} 被锁定，将临时锁定30分钟")
                    try:
                        with conn_lock:
                            self.ban_account_temporarily(account_id, 1800)  # 30分钟
                    except Exception as e:
                        log.error(f"临时封禁账号 {account_id} 时发生错误: {str(e)}")
                    with banned_lock:
                        banned_accounts.append(account_id)
                    
                    # 更新Redis中的状态
                    if self.redis_client:
                        unban_time = datetime.now() + timedelta(seconds=1800)
                        
                        # 更新状态信息
                        status_data = {
                            "is_available": 0,
                            "is_permanently_banned": 0
                        }
                        self.redis_client.hset(self.REDIS_COOKIE_STATUS_KEY, account_id, json.dumps(status_data, ensure_ascii=False))
                        
                        # 更新封禁信息
                        ban_data = {
                            "temp_ban_until": unban_time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        self.redis_client.hset(self.REDIS_COOKIE_BAN_KEY, account_id, json.dumps(ban_data, ensure_ascii=False))
                    
                elif status == 10002:
                    # 状态为10002表示请求错误，不需要任何操作，但仍视为有效cookie
                    log.info(f"账号 {account_id} 请求错误，但仍视为有效: {message}")
                    with valid_lock:
                        valid_accounts.append(account_id)
                else:
                    # 其他状态视为未登录，也需要永久封禁
                    log.warning(f"账号 {account_id} 状态异常: {status}, message: {message}，将被永久锁定")
                    try:
                        with conn_lock:
                            self.ban_account_permanently(account_id)
                    except Exception as e:
                        log.error(f"永久封禁账号 {account_id} 时发生错误: {str(e)}")
                    with banned_lock:
                        banned_accounts.append(account_id)
                    
                    # Redis中直接删除该账号数据
                    if self.redis_client:
                        self.redis_client.hdel(self.REDIS_COOKIES_KEY, account_id)
                        self.redis_client.hdel(self.REDIS_COOKIE_STATUS_KEY, account_id)
                        self.redis_client.hdel(self.REDIS_COOKIE_BAN_KEY, account_id)
            except Exception as e:
                log.error(f"测试账号 {account_id} 时发生错误: {str(e)}")
                with not_login_lock:
                    not_login_accounts.append(account_id)
            finally:
                # 确保连接被关闭
                if local_conn and hasattr(local_conn, 'close'):
                    try:
                        local_conn.close()
                    except:
                        pass
        
        # 使用线程池并行测试
        total_accounts = len(account_ids)
        max_workers = min(8, total_accounts)  # 最多5个线程，避免创建过多线程
        
        if max_workers == 0:
            log.warning("没有可用账号需要测试")
            return {
                "valid_accounts": [],
                "banned_accounts": [],
                "not_login_accounts": [],
                "total_tested": 0,
                "valid_count": 0,
                "banned_count": 0,
                "not_login_count": 0
            }
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            futures = [executor.submit(test_single_account, account_id) for account_id in account_ids]
            
            # 显示进度
            completed = 0
            for future in as_completed(futures):
                completed += 1
                if completed % 10 == 0 or completed == total_accounts:
                    log.info(f"测试进度: {completed}/{total_accounts} ({completed/total_accounts*100:.1f}%)")
                # 获取结果（如果有异常会在这里抛出）
                try:
                    future.result()
                except Exception as e:
                    log.error(f"线程执行异常: {e}")
        
        # 更新Redis中的可用账号计数
        if self.redis_client:
            self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, len(valid_accounts))
            self.redis_client.expire(self.REDIS_COOKIE_COUNT_KEY, self.REDIS_EXPIRE)
        
        # 统计结果
        total_tested = len(account_ids)
        valid_count = len(valid_accounts)
        banned_count = len(banned_accounts)
        not_login_count = len(not_login_accounts)
        
        log.info(f"Cookie可用性测试完成: 总测试 {total_tested} 个账号, "
                 f"有效 {valid_count} 个, 被封禁 {banned_count} 个, 未登录 {not_login_count} 个")
        
        # 返回测试结果
        return {
            "valid_accounts": valid_accounts,
            "banned_accounts": banned_accounts,
            "not_login_accounts": not_login_accounts,
            "total_tested": total_tested,
            "valid_count": valid_count,
            "banned_count": banned_count,
            "not_login_count": not_login_count
        }

    def get_cookie_by_account_id(self, account_id):
        """
        获取指定账号ID的完整cookie字典
        
        Args:
            account_id: 账号ID
            
        Returns:
            dict: 完整的cookie字典，如果没有找到则返回None
        """
        try:
            cookies = self.get_cookies_by_account_id(account_id)
            if not cookies:
                log.warning(f"未找到账号 {account_id} 的cookie记录")
                return None
            
            cookie_dict = {}
            for cookie in cookies:
                # 检查cookie是否可用
                if not cookie['is_available'] or cookie['is_permanently_banned']:
                    continue
                if cookie['temp_ban_until'] and cookie['temp_ban_until'] > datetime.now():
                    continue
                if cookie['expire_time'] and cookie['expire_time'] < datetime.now():
                    continue
                    
                cookie_dict[cookie['cookie_name']] = cookie['cookie_value']
            
            if not cookie_dict:
                log.warning(f"账号 {account_id} 没有可用的cookie")
                return None
            
            log.debug(f"成功获取账号 {account_id} 的cookie字典，包含 {len(cookie_dict)} 个键值对")
            return cookie_dict
        except Exception as e:
            log.error(f"获取账号 {account_id} 的cookie字典失败: {str(e)}")
            return None

    def test_account_cookie_availability(self, account_id) -> Dict[str, Any]:
        """测试单个账号Cookie的可用性
        
        测试条件：
        - 状态为0表示cookie有效可用
        - 状态为10000表示账号未登录，需要将该账号的所有cookie永久锁定
        - 状态为10001表示账号被锁定，需要将对应记录在MySQL中临时锁定30分钟
        - 状态为10002表示请求错误，不需要任何操作，但仍视为有效cookie
        
        Args:
            account_id: 要测试的账号ID
            
        Returns:
            Dict[str, Any]: 包含测试结果的字典
        """
        log.info(f"开始测试账号 {account_id} 的Cookie可用性")
        
        # 获取账号的cookie
        cookies = self.get_cookie_by_account_id(account_id)
        if not cookies:
            log.warning(f"账号 {account_id} 没有可用的cookie")
            
            # 更新Redis中的状态
            if self.redis_client:
                self.redis_client.hdel(self.REDIS_COOKIES_KEY, account_id)
                self.redis_client.hdel(self.REDIS_COOKIE_STATUS_KEY, account_id)
                self.redis_client.hdel(self.REDIS_COOKIE_BAN_KEY, account_id)
                
                # 更新计数
                available_count = self.get_redis_available_cookie_count()
                if available_count > 0:
                    self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, available_count - 1)
            
            return {
                "account_id": account_id,
                "status": -1,
                "message": "没有可用的cookie",
                "is_valid": False,
                "action_taken": "无"
            }
        
        # 测试参数
        city_number = "911"  # 北京
        word = "电脑"
        # 计算日期范围（最近30天）
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        startDate = start_date.strftime("%Y-%m-%d")
        endDate = end_date.strftime("%Y-%m-%d")
        
        # 创建UserAgent实例
        ua = UserAgent()
        
        try:
            # 组装cookie字符串
            cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
            url_cipyter = f'https://index.baidu.com/v2/main/index.html#/trend/{word}?words={word}'
        
            # 获取cipher-text
            try:
                with open('/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/utils/Cipher-Text.js', 'r') as f:
                    js = f.read()
                    ctx = execjs.compile(js)
                cipyer_text = ctx.call('ascToken', url_cipyter, ua.random)
            except Exception as e:
                log.error(f"生成cipher-text失败: {str(e)}")
                cipyer_text = ""
        
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Cache-Control': 'no-cache',
                'Cipher-Text': cipyer_text,
                'Connection': 'keep-alive',
                'Pragma': 'no-cache',
                'Referer': 'https://index.baidu.com/v2/main/index.html',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': ua.random,
                'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                "Cookie": cookie_str
            }
            
            # 构建请求URL
            url = f'https://index.baidu.com/api/SearchApi/index?area={city_number}&word=[[{{"name":"{word}","wordType":1}}]]&startDate={startDate}&endDate={endDate}'
            
            # 发送请求
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()
            
            # 检查响应状态
            status = data.get("status", -1)
            message = data.get("message", "")
            
            log.info(f"账号 {account_id} 测试结果: status={status}, message={message}")
            
            # 根据状态执行不同操作
            action_taken = "无"
            is_valid = False
            
            if status == 0:
                # 状态为0表示cookie有效可用
                log.info(f"账号 {account_id} 的cookie有效可用")
                is_valid = True
                action_taken = "保持可用状态"
                
                # 确保Redis状态正确
                if self.redis_client:
                    all_cookies = self.get_cookies_by_account_id(account_id)
                    if all_cookies:
                        # 组装cookie字典
                        cookie_dict = {}
                        for cookie in all_cookies:
                            cookie_dict[cookie['cookie_name']] = cookie['cookie_value']
                        
                            # 更新Redis中的状态
                            self._save_cookie_to_redis(account_id, cookie_dict, True, False, None)
                
            elif status == 10000:
                # 状态为10000表示账号未登录，需要将该账号的所有cookie永久锁定
                log.warning(f"账号 {account_id} 未登录，将被永久锁定")
                self.ban_account_permanently(account_id)
                action_taken = "永久锁定账号"
                
                # Redis中直接删除该账号数据
                if self.redis_client:
                    self.redis_client.hdel(self.REDIS_COOKIES_KEY, account_id)
                    self.redis_client.hdel(self.REDIS_COOKIE_STATUS_KEY, account_id)
                    self.redis_client.hdel(self.REDIS_COOKIE_BAN_KEY, account_id)
                    
                    # 更新计数
                    available_count = self.get_redis_available_cookie_count()
                    if available_count > 0:
                        self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, available_count - 1)
                
            elif status == 10001:
                # 状态为10001表示账号被锁定，需要将对应记录在MySQL中临时锁定30分钟
                log.warning(f"账号 {account_id} 被锁定，将临时锁定30分钟")
                self.ban_account_temporarily(account_id, 1800)  # 30分钟
                action_taken = "临时锁定账号30分钟"
                
                # 更新Redis中的状态
                if self.redis_client:
                    unban_time = datetime.now() + timedelta(seconds=1800)
                    
                    # 更新状态信息
                    status_data = {
                        "is_available": 0,
                        "is_permanently_banned": 0
                    }
                    self.redis_client.hset(self.REDIS_COOKIE_STATUS_KEY, account_id, json.dumps(status_data, ensure_ascii=False))
                    
                    # 更新封禁信息
                    ban_data = {
                        "temp_ban_until": unban_time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    self.redis_client.hset(self.REDIS_COOKIE_BAN_KEY, account_id, json.dumps(ban_data, ensure_ascii=False))
                    
                    # 更新计数
                    available_count = self.get_redis_available_cookie_count()
                    if available_count > 0:
                        self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, available_count - 1)
                
            elif status == 10002:
                # 状态为10002表示请求错误，不需要任何操作，但仍视为有效cookie
                log.info(f"账号 {account_id} 请求错误，但仍视为有效: {message}")
                is_valid = True
                action_taken = "请求错误，但视为有效"
            else:
                # 其他状态视为未登录，也需要永久封禁
                log.warning(f"账号 {account_id} 状态异常: {status}, message: {message}，将被永久锁定")
                self.ban_account_permanently(account_id)
                action_taken = "永久锁定账号"
                
                # Redis中直接删除该账号数据
                if self.redis_client:
                    self.redis_client.hdel(self.REDIS_COOKIES_KEY, account_id)
                    self.redis_client.hdel(self.REDIS_COOKIE_STATUS_KEY, account_id)
                    self.redis_client.hdel(self.REDIS_COOKIE_BAN_KEY, account_id)
                    
                    # 更新计数
                    available_count = self.get_redis_available_cookie_count()
                    if available_count > 0:
                        self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, available_count - 1)
            
            # 返回测试结果
            return {
                "account_id": account_id,
                "status": status,
                "message": message,
                "is_valid": is_valid,
                "action_taken": action_taken
            }
            
        except Exception as e:
            log.error(f"测试账号 {account_id} 时发生错误: {str(e)}")
            return {
                "account_id": account_id,
                "status": -1,
                "message": f"测试过程中发生错误: {str(e)}",
                "is_valid": False,
                "action_taken": "无"
            }

    def __del__(self):
        """析构函数，确保连接被关闭"""
        self.close()

    def update_ab_sr_for_all_accounts(self):
        """
        更新所有账号的ab_sr cookie值
        
        为每个账号更新ab_sr cookie值，如果账号没有ab_sr字段则新增
        
        Returns:
            dict: 包含更新结果的字典
                {
                    'updated_count': 更新成功的账号数量,
                    'failed_count': 更新失败的账号数量,
                    'added_count': 新增ab_sr字段的账号数量
                }
        """
        try:
            # 获取所有账号ID
            cursor = self._get_cursor()
            cursor.execute("SELECT DISTINCT account_id FROM cookies")
            accounts = cursor.fetchall()
            
            # 更新计数器
            updated_count = 0
            failed_count = 0
            added_count = 0
            
            # 获取新的ab_sr值
            updater = AbSrUpdater()
            new_ab_sr = updater.update_ab_sr()
            
            if not new_ab_sr:
                return {
                    'updated_count': 0,
                    'failed_count': len(accounts),
                    'added_count': 0,
                    'error': 'Failed to get new ab_sr value'
                }
            
            # 遍历所有账号
            for account in accounts:
                account_id = account['account_id']
                
                # 查询账号是否已有ab_sr cookie
                cursor.execute(
                    "SELECT id, is_available, is_permanently_banned, temp_ban_until FROM cookies "
                    "WHERE account_id = %s AND cookie_name = 'ab_sr'",
                    (account_id,)
                )
                ab_sr_cookie = cursor.fetchone()
                
                if ab_sr_cookie:
                    # 已有ab_sr，更新它
                    cursor.execute(
                        "UPDATE cookies SET cookie_value = %s, last_updated = NOW() "
                        "WHERE id = %s",
                        (new_ab_sr, ab_sr_cookie['id'])
                    )
                    updated_count += 1
                else:
                    # 没有ab_sr，需要新增
                    # 获取账号的其他cookie状态信息
                    cursor.execute(
                        "SELECT is_available, is_permanently_banned, temp_ban_until "
                        "FROM cookies WHERE account_id = %s LIMIT 1",
                        (account_id,)
                    )
                    account_status = cursor.fetchone()
                    
                    if account_status:
                        # 新增ab_sr cookie
                        cursor.execute(
                            "INSERT INTO cookies (account_id, cookie_name, cookie_value, "
                            "is_available, is_permanently_banned, temp_ban_until) "
                            "VALUES (%s, 'ab_sr', %s, %s, %s, %s)",
                            (
                                account_id, 
                                new_ab_sr,
                                account_status['is_available'],
                                account_status['is_permanently_banned'],
                                account_status['temp_ban_until']
                            )
                        )
                        added_count += 1
                    else:
                        failed_count += 1
            
            # 提交数据库更改
            self.conn.commit()
            
            # 同步到Redis
            self.sync_to_redis()
            
            return {
                'updated_count': updated_count,
                'failed_count': failed_count,
                'added_count': added_count
            }
            
        except Exception as e:
            self.conn.rollback()
            log.error(f"更新ab_sr失败: {e}")
            return {
                'updated_count': 0,
                'failed_count': len(accounts) if 'accounts' in locals() else 0,
                'added_count': 0,
                'error': str(e)
            }
