"""
Cookie管理器 - 提供对数据库中cookie的CRUD操作
"""
import json
import time
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path
import requests
from fake_useragent import UserAgent
from typing import Dict, List, Tuple, Any, Optional, Set, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import execjs
import redis
import traceback

from src.core.logger import log
from src.core.config import REDIS_CONFIG, CIPHER_TEXT_JS_PATH
from src.data.repositories.cookie_repository import cookie_repo

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
        """初始化"""
        self.repo = cookie_repo
        
        # 初始化Redis连接
        self.redis_client = None
        self.redis_config = REDIS_CONFIG
        self._connect_redis()

    def _get_cipher_js_path(self):
        """获取Cipher-Text.js文件的绝对路径"""
        if not os.path.exists(CIPHER_TEXT_JS_PATH):
            log.error(f"Cipher-Text.js 文件不存在: {CIPHER_TEXT_JS_PATH}")
            raise FileNotFoundError(f"找不到 Cipher-Text.js 文件: {CIPHER_TEXT_JS_PATH}")
        return str(CIPHER_TEXT_JS_PATH)
    
    def _connect_redis(self):
        """连接Redis"""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_config['host'],
                port=self.redis_config['port'],
                db=self.redis_config['db'],
                password=self.redis_config['password'],
                decode_responses=True  # 自动将字节解码为字符串
            )
        except Exception as e:
            log.error(f"连接Redis失败: {e}")
            self.redis_client = None
            
    def close(self):
        """关闭连接"""
        if self.redis_client:
            self.redis_client.close()
            self.redis_client = None
    
    def sync_to_redis(self):
        """将MySQL中的cookie数据同步到Redis"""
        try:
            # log.info("开始同步cookie数据到Redis...")
            
            # 清除Redis中的旧数据
            self._clear_redis_cookies()
            
            # 获取所有可用且未被永久封禁的cookie
            # Note: Repo returns CookieModel objects
            cookies = self.repo.get_available_cookies()
            
            # 按账号ID分组
            cookies_by_account = {}
            for cookie in cookies:
                account_id = cookie.account_id
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
                    cookie_dict[cookie.cookie_name] = cookie.cookie_value
                    
                    # 如果任一cookie不可用或被永久封禁，则整个账号被视为不可用
                    if not cookie.is_available:
                        is_available = False
                    if cookie.is_permanently_banned:
                        is_permanently_banned = True
                    
                    # 记录临时封禁时间（取最大值）
                    if cookie.temp_ban_until:
                        if temp_ban_until is None or cookie.temp_ban_until > temp_ban_until:
                            temp_ban_until = cookie.temp_ban_until
                
                # 将cookie数据存入Redis
                self._save_cookie_to_redis(account_id, cookie_dict, is_available, is_permanently_banned, temp_ban_until)
                
                if is_available and not is_permanently_banned and (temp_ban_until is None or temp_ban_until < datetime.now()):
                    available_count += 1
            
            # 更新可用cookie数量
            if self.redis_client:
                self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, available_count)
                self.redis_client.expire(self.REDIS_COOKIE_COUNT_KEY, self.REDIS_EXPIRE)
            
            log.info(f"成功同步 {len(cookies_by_account)} 个账号的cookie数据到Redis，其中 {available_count} 个可用")
            return True
        except Exception as e:
            log.error(f"同步cookie数据到Redis失败: {e}")
            import traceback
            log.error(traceback.format_exc())
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
    
    def parse_cookie_string(self, cookie_string):
        """解析完整的cookie字符串为字典"""
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
        """
        try:
            # 处理cookie数据
            if isinstance(cookie_data, str):
                try:
                    cookie_dict = json.loads(cookie_data)
                except:
                    cookie_dict = self.parse_cookie_string(cookie_data)
            elif isinstance(cookie_data, dict):
                cookie_dict = cookie_data
            else:
                return False
            
            if expire_time is None:
                expire_time = datetime.now() + timedelta(days=365)  # 默认一年后过期
            
            # 使用Repo保存
            success = self.repo.upsert_cookies(account_id, cookie_dict, expire_time)
            
            if success:
                # 更新Redis中的数据
                if self.redis_client:
                    # 获取更新后的cookie数据 (from dict directly since we just saved it and assume success)
                    # 最好还是从DB查一次，或者直接用传入的数据
                    # 这里保持原逻辑架构：更新Redis
                    
                    self._save_cookie_to_redis(account_id, cookie_dict, True, False, None)
                    
                    # 更新可用cookie数量
                    available_count = self.get_redis_available_cookie_count()
                    self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, available_count + 1)
            
            return success
        except Exception as e:
            log.error(f"添加cookie失败: {e}")
            return False
    
    def delete_by_account_id(self, account_id):
        """根据账号ID删除所有相关cookie"""
        try:
            deleted_count = self.repo.delete_by_account_id(account_id)
            
            # 从Redis中删除相关数据
            if deleted_count > 0 and self.redis_client:
                # 检查是否是可用的cookie, 更新计数
                status_json = self.redis_client.hget(self.REDIS_COOKIE_STATUS_KEY, account_id)
                if status_json:
                    status = json.loads(status_json)
                    is_available = status.get("is_available") == 1
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
            return 0
    
    def update_cookie(self, cookie_id, update_data):
        """更新cookie字段"""
        try:
            # 先获取当前cookie的信息，包括account_id
            current_cookie = self.repo.get_cookie_by_id(cookie_id)
            if not current_cookie:
                return False
            
            account_id = current_cookie.account_id
            
            # 更新
            success = self.repo.update_cookie_fields(cookie_id, update_data)
            
            # 如果更新成功，同步到Redis
            if success and self.redis_client:
                # 获取更新后的account的所有cookie
                # 重用 get_cookies_by_account_id which returns dicts in old style?
                # No, we need to adapt Repo models to logic
                
                cookies = self.repo.get_cookies_by_account_id(account_id)
                
                if cookies:
                    cookie_dict = {}
                    is_available = True
                    is_permanently_banned = False
                    temp_ban_until = None
                    
                    for cookie in cookies:
                        cookie_dict[cookie.cookie_name] = cookie.cookie_value
                        if not cookie.is_available:
                            is_available = False
                        if cookie.is_permanently_banned:
                            is_permanently_banned = True
                        if cookie.temp_ban_until:
                            if temp_ban_until is None or cookie.temp_ban_until > temp_ban_until:
                                temp_ban_until = cookie.temp_ban_until
                    
                    # 更新Redis
                    if is_permanently_banned:
                        self.redis_client.hdel(self.REDIS_COOKIES_KEY, account_id)
                        self.redis_client.hdel(self.REDIS_COOKIE_STATUS_KEY, account_id)
                        self.redis_client.hdel(self.REDIS_COOKIE_BAN_KEY, account_id)
                    else:
                        self._save_cookie_to_redis(account_id, cookie_dict, is_available, False, temp_ban_until)
                    
                    # 重新计算可用数量 (简化逻辑，直接全量同步计数可能太慢，这里沿用原逻辑：遍历Redis)
                    # 原逻辑: available_count += 1 loop
                    # 既然已经封装在 _sync_cookie_status_to_redis 这里
                    # 我们简单地重新获取所有可用计数
                    # 或者我们可以调用 repo.get_available_account_ids() 获取总数
                    
                    all_available_ids = self.repo.get_available_account_ids()
                    self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, len(all_available_ids))
                    
                    log.info(f"已更新Redis中账号 {account_id} 的cookie数据")
            
            return success
        except Exception as e:
            log.error(f"更新cookie失败: {e}")
            return False
            
    def ban_account_permanently(self, account_id):
        """永久封禁指定账号ID的所有cookie"""
        try:
            banned_count = self.repo.ban_account_permanently(account_id)
            
            if banned_count > 0 and self.redis_client:
                self.redis_client.hdel(self.REDIS_COOKIES_KEY, account_id)
                self.redis_client.hdel(self.REDIS_COOKIE_STATUS_KEY, account_id)
                self.redis_client.hdel(self.REDIS_COOKIE_BAN_KEY, account_id)
                
                available_count = self.get_redis_available_cookie_count()
                if available_count > 0:
                    self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, available_count - 1)
                
                log.info(f"已从Redis中删除永久封禁的账号 {account_id} 数据")
            
            return banned_count
        except Exception as e:
            log.error(f"永久封禁账号失败: {e}")
            return 0
    
    def ban_account_temporarily(self, account_id, duration_seconds=1800):
        """暂时封禁"""
        try:
            unban_time = datetime.now() + timedelta(seconds=duration_seconds)
            banned_count = self.repo.ban_account_temporarily(account_id, unban_time)
            
            if banned_count > 0 and self.redis_client:
                status_data = {"is_available": 0, "is_permanently_banned": 0}
                self.redis_client.hset(self.REDIS_COOKIE_STATUS_KEY, account_id, json.dumps(status_data, ensure_ascii=False))
                
                ban_data = {"temp_ban_until": unban_time.strftime("%Y-%m-%d %H:%M:%S")}
                self.redis_client.hset(self.REDIS_COOKIE_BAN_KEY, account_id, json.dumps(ban_data, ensure_ascii=False))
                
                available_count = self.get_redis_available_cookie_count()
                if available_count > 0:
                    self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, available_count - 1)
                
                log.info(f"已更新Redis中临时封禁的账号 {account_id} 数据，封禁至 {unban_time}")
            
            return banned_count
        except Exception as e:
            log.error(f"暂时封禁账号失败: {e}")
            return 0
    
    def unban_account(self, account_id):
        """解封指定账号ID的所有cookie（只解封临时封禁的）"""
        try:
            unbanned_count = self.repo.unban_account(account_id)
            
            if unbanned_count > 0 and self.redis_client:
                # 获取数据更新Redis
                # Get raw models
                cookies = self.repo.get_cookies_by_account_id(account_id)
                if cookies:
                    cookie_dict = {}
                    for cookie in cookies:
                        cookie_dict[cookie.cookie_name] = cookie.cookie_value
                    
                    # Status
                    status_data = {"is_available": 1, "is_permanently_banned": 0}
                    self.redis_client.hset(self.REDIS_COOKIE_STATUS_KEY, account_id, json.dumps(status_data, ensure_ascii=False))
                    self.redis_client.hdel(self.REDIS_COOKIE_BAN_KEY, account_id)
                    
                    cookie_data = {"account_id": account_id, "cookie": cookie_dict}
                    self.redis_client.hset(self.REDIS_COOKIES_KEY, account_id, json.dumps(cookie_data, ensure_ascii=False))
                    
                    available_count = self.get_redis_available_cookie_count()
                    self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, available_count + 1)
                    
                    log.info(f"已更新Redis中解封的账号 {account_id} 数据")
            
            return unbanned_count
        except Exception as e:
            log.error(f"解封账号失败: {e}")
            return 0
            
    def force_unban_account(self, account_id):
        """强制解封"""
        try:
            unbanned_count = self.repo.force_unban_account(account_id)
            
            if unbanned_count > 0 and self.redis_client:
                cookies = self.repo.get_cookies_by_account_id(account_id)
                if cookies:
                    cookie_dict = {}
                    for cookie in cookies:
                        cookie_dict[cookie.cookie_name] = cookie.cookie_value
                    
                    self._save_cookie_to_redis(account_id, cookie_dict, True, False, None)
                    available_count = self.get_redis_available_cookie_count()
                    self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, available_count + 1)
                    
                    log.info(f"已更新Redis中强制解封的账号 {account_id} 数据")
            return unbanned_count
        except Exception as e:
            log.error(f"强制解封账号失败: {e}")
            return 0
            
    def get_cookies_by_account_id(self, account_id):
        """
        获取指定账号ID的所有cookie (返回字典列表，保持兼容性)
        """
        try:
            models = self.repo.get_cookies_by_account_id(account_id)
            # Convert models to dicts to match old API return: cursor.fetchall()
            return [m.model_dump() for m in models]
        except Exception as e:
            log.error(f"获取cookie失败: {e}")
            return []
            
    def get_available_cookies(self):
        """获取所有可用的cookie"""
        try:
            models = self.repo.get_available_cookies()
            return [m.model_dump() for m in models]
        except Exception as e:
            log.error(f"获取可用cookie失败: {e}")
            return []
            
    def get_cookies_by_account_ids(self, account_ids=None):
        """按账号ID分组获取cookie"""
        try:
            if account_ids:
                models = self.repo.get_cookies_by_account_ids(account_ids)
            else:
                models = self.repo.get_available_cookies()
            
            cookies = [m.model_dump() for m in models]
            
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
        """获取所有可用账号的完整cookie字典"""
        try:
            grouped_cookies = self.get_cookies_by_account_ids(account_ids)
            assembled_cookies = []
            
            for account_id, cookies in grouped_cookies.items():
                cookie_dict = {}
                for cookie in cookies:
                    cookie_dict[cookie['cookie_name']] = cookie['cookie_value']
                
                if cookie_dict:
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
        """获取所有可用的账号ID列表"""
        try:
            return self.repo.get_available_account_ids()
        except Exception as e:
            log.error(f"获取可用账号ID失败: {e}")
            return []
            
    def update_account_id(self, old_account_id, new_account_id):
        """更新账号ID"""
        try:
            # Check Redis for old ID
            redis_has_old = False
            if self.redis_client:
                redis_has_old = self.redis_client.hexists(self.REDIS_COOKIES_KEY, old_account_id)
            
            updated_count = self.repo.update_account_id(old_account_id, new_account_id)
            
            if updated_count > 0 and redis_has_old and self.redis_client:
                 # 获取旧账号的Redis数据
                cookie_json = self.redis_client.hget(self.REDIS_COOKIES_KEY, old_account_id)
                status_json = self.redis_client.hget(self.REDIS_COOKIE_STATUS_KEY, old_account_id)
                ban_json = self.redis_client.hget(self.REDIS_COOKIE_BAN_KEY, old_account_id)
                
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
            return 0
            
    def check_and_update_cookie_status(self):
        """检查并更新cookie状态，将临时封禁过期的cookie恢复可用"""
        try:
            # 获取需要解封的账号
            unlocked_accounts = self.repo.get_expired_temp_bans()
            
            # 使用Repo批量解封
            updated_count = self.repo.unlock_accounts(unlocked_accounts)
            
            if updated_count > 0:
                log.info(f"已解封临时封禁的cookie记录，涉及 {len(unlocked_accounts)} 个账号")
                
                # Update Redis for each account
                for account_id in unlocked_accounts:
                    cookies = self.get_cookies_by_account_id(account_id)
                    if cookies:
                        cookie_dict = {}
                        for cookie in cookies:
                            cookie_dict[cookie['cookie_name']] = cookie['cookie_value']
                        
                        if self.redis_client:
                            status_data = {"is_available": 1, "is_permanently_banned": 0}
                            self.redis_client.hset(self.REDIS_COOKIE_STATUS_KEY, account_id, json.dumps(status_data, ensure_ascii=False))
                            self.redis_client.hdel(self.REDIS_COOKIE_BAN_KEY, account_id)
                            
                            cookie_data = {"account_id": account_id, "cookie": cookie_dict}
                            self.redis_client.hset(self.REDIS_COOKIES_KEY, account_id, json.dumps(cookie_data, ensure_ascii=False))
                
                # Update total available count
                if self.redis_client:
                    all_ids = self.repo.get_available_account_ids()
                    self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, len(all_ids))
            
            # Stats
            available_ids = self.repo.get_available_account_ids()
            # 获取总账号数 (Repo helper needed or just execute select)
            # For simplicity let's stick to what we have
            total_count = 0 # Placeholder if we don't add count method to Repo
            # Actually let's just leave it 0 or add a method.
            # Adding count method to Repo later if needed.
            
            return {
                'updated_count': updated_count,
                'available_count': len(available_ids),
                'total_count': total_count,
                'unlocked_accounts': unlocked_accounts
            }
        except Exception as e:
            log.error(f"更新cookie状态失败: {e}")
            log.error(traceback.format_exc())
            return {'error': str(e)}

    def cleanup_expired_cookies(self):
        """清理已过期的cookie"""
        try:
            return self.repo.cleanup_expired_cookies()
        except Exception as e:
            log.error(f"清理过期cookie失败: {e}")
            return 0
            
    def get_cookie_by_account_id(self, account_id):
        """获取指定账号ID的完整cookie字典"""
        try:
            cookies = self.get_cookies_by_account_id(account_id)
            if not cookies:
                log.warning(f"未找到账号 {account_id} 的cookie记录")
                return None
            
            cookie_dict = {}
            for cookie in cookies:
                # 检查cookie是否可用
                if not cookie.get('is_available') or cookie.get('is_permanently_banned'):
                    continue
                if cookie.get('temp_ban_until') and cookie.get('temp_ban_until') > datetime.now():
                    continue
                if cookie.get('expire_time') and cookie.get('expire_time') < datetime.now():
                    continue
                    
                cookie_dict[cookie['cookie_name']] = cookie['cookie_value']
            
            if not cookie_dict:
                log.warning(f"账号 {account_id} 没有可用的cookie")
                return None
            
            return cookie_dict
        except Exception as e:
            log.error(f"获取账号 {account_id} 的cookie字典失败: {str(e)}")
            return None
            
    def test_cookies_availability(self) -> Dict[str, Any]:
        """测试所有可用Cookie的可用性"""
        log.info("开始测试Cookie可用性")
        
        # 获取所有可用的账号ID
        account_ids = self.get_available_account_ids()
        log.info(f"获取到 {len(account_ids)} 个可用账号")
        
        valid_accounts = []
        banned_accounts = []
        not_login_accounts = []
        
        # 创建线程锁
        valid_lock = threading.Lock()
        banned_lock = threading.Lock()
        not_login_lock = threading.Lock()
        
        # 定义单个账号测试函数
        def test_single_account(account_id):
            try:
                # 获取账号的cookie
                # 直接调用 repo/manager，因 session_scope 是线程安全的
                cookies = self.get_cookie_by_account_id(account_id)
                
                if not cookies:
                    log.warning(f"账号 {account_id} 没有可用的cookie")
                    with not_login_lock:
                        not_login_accounts.append(account_id)
                    self.ban_account_permanently(account_id)
                    return
                
                # 测试参数
                city_number = "911"
                word = "电脑"
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                startDate = start_date.strftime("%Y-%m-%d")
                endDate = end_date.strftime("%Y-%m-%d")
                
                ua = UserAgent()
                cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
                url_cipyter = f'https://index.baidu.com/v2/main/index.html#/trend/{word}?words={word}'
            
                try:
                    cipher_js_path = self._get_cipher_js_path()
                    with open(cipher_js_path, 'r', encoding='utf-8') as f:
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
                
                url = f'https://index.baidu.com/api/SearchApi/index?area={city_number}&word=[[{{"name":"{word}","wordType":1}}]]&startDate={startDate}&endDate={endDate}'
                
                response = requests.get(url, headers=headers, timeout=10)
                data = response.json()
                
                status = data.get("status", -1)
                message = data.get("message", "")
                
                if status == 0:
                    with valid_lock:
                        valid_accounts.append(account_id)
                    # Sync Redis
                    if self.redis_client:
                         cookies_list = self.get_cookies_by_account_id(account_id)
                         if cookies_list:
                            cookie_dict = {}
                            for c in cookies_list:
                                cookie_dict[c['cookie_name']] = c['cookie_value']
                            self._save_cookie_to_redis(account_id, cookie_dict, True, False, None)
                    
                elif status == 10000:
                    log.warning(f"账号 {account_id} 未登录")
                    try:
                        self.ban_account_permanently(account_id)
                    except Exception as e:
                        log.error(f"Error banning {account_id}: {e}")
                    with not_login_lock:
                        not_login_accounts.append(account_id)
                    
                elif status == 10001:
                    log.warning(f"账号 {account_id} 被锁定")
                    try:
                        self.ban_account_temporarily(account_id, 1800)
                    except Exception as e:
                        log.error(f"Error temp banning {account_id}: {e}")
                    with banned_lock:
                        banned_accounts.append(account_id)
                    
                elif status == 10002:
                    log.info(f"账号 {account_id} 请求错误但有效")
                    with valid_lock:
                        valid_accounts.append(account_id)
                else:
                    log.warning(f"账号 {account_id} 异常 {status}")
                    try:
                        self.ban_account_permanently(account_id)
                    except Exception as e:
                        log.error(f"Error banning {account_id}: {e}")
                    with banned_lock:
                        banned_accounts.append(account_id)

            except Exception as e:
                log.error(f"测试账号 {account_id} 错误: {e}")
                with not_login_lock:
                    not_login_accounts.append(account_id)

        # Thread Pool
        total_accounts = len(account_ids)
        max_workers = min(8, total_accounts)
        
        if max_workers == 0:
             return {
                "valid_accounts": [], "banned_accounts": [], "not_login_accounts": [],
                "total_tested": 0, "valid_count": 0, "banned_count": 0, "not_login_count": 0
            }
            
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(test_single_account, aid) for aid in account_ids]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    log.error(f"Thread exception: {e}")
        
        if self.redis_client:
            self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, len(valid_accounts))
            self.redis_client.expire(self.REDIS_COOKIE_COUNT_KEY, self.REDIS_EXPIRE)
            
        return {
            "valid_accounts": valid_accounts, "banned_accounts": banned_accounts, "not_login_accounts": not_login_accounts,
            "total_tested": total_accounts, "valid_count": len(valid_accounts),
            "banned_count": len(banned_accounts), "not_login_count": len(not_login_accounts)
        }

    def test_account_cookie_availability(self, account_id) -> Dict[str, Any]:
        """测试单个账号Cookie的可用性"""
        log.info(f"开始测试账号 {account_id} 的Cookie可用性")
        
        # Reuse logic is tricky because above function is complex closure
        # But we can assume calling the same logic inline
        
        cookies = self.get_cookie_by_account_id(account_id)
        if not cookies:
             # Logic to remove from Redis
             if self.redis_client:
                self.redis_client.hdel(self.REDIS_COOKIES_KEY, account_id)
                self.redis_client.hdel(self.REDIS_COOKIE_STATUS_KEY, account_id)
                self.redis_client.hdel(self.REDIS_COOKIE_BAN_KEY, account_id)
             return {"account_id": account_id, "status": -1, "message": "No cookies", "is_valid": False}
        
        # Test logic (simplified copy from above to ensure working standalone)
        city_number = "911"
        word = "电脑"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        startDate = start_date.strftime("%Y-%m-%d")
        endDate = end_date.strftime("%Y-%m-%d")
        
        ua = UserAgent()
        try:
             cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
             url_cipyter = f'https://index.baidu.com/v2/main/index.html#/trend/{word}?words={word}'
             
             try:
                 cipher_js_path = self._get_cipher_js_path()
                 with open(cipher_js_path, 'r', encoding='utf-8') as f:
                     js = f.read()
                 ctx = execjs.compile(js)
                 cipyer_text = ctx.call('ascToken', url_cipyter, ua.random)
             except Exception:
                 cipyer_text = ""
                 
             headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Cache-Control': 'no-cache',
                'Cipher-Text': cipyer_text,
                'Connection': 'keep-alive',
                'Pragma': 'no-cache',
                'Referer': 'https://index.baidu.com/v2/main/index.html',
                'User-Agent': ua.random,
                "Cookie": cookie_str
            }
             url = f'https://index.baidu.com/api/SearchApi/index?area={city_number}&word=[[{{"name":"{word}","wordType":1}}]]&startDate={startDate}&endDate={endDate}'
             response = requests.get(url, headers=headers, timeout=10)
             data = response.json()
             status = data.get("status", -1)
             message = data.get("message", "")
             
             log.info(f"账号 {account_id} 测试结果: status={status}")
             
             if status == 0:
                 return {"account_id": account_id, "status": 0, "message": "OK", "is_valid": True}
             else:
                 return {"account_id": account_id, "status": status, "message": message, "is_valid": False}
                 
        except Exception as e:
             log.error(f"Test failed: {e}")
             return {"account_id": account_id, "status": -1, "message": str(e), "is_valid": False}


# 创建单例
cookie_manager = CookieManager()

def get_cookie_manager():
    return cookie_manager
