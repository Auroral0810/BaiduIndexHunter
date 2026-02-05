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
from src.engine.crypto.ab_sr_updater import AbSrUpdater

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
        
        # 初始化 ab_sr 更新器
        try:
            self.ab_sr_updater = AbSrUpdater()
        except Exception as e:
            log.error(f"初始化 AbSrUpdater 失败: {e}")
            self.ab_sr_updater = None

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

    def _get_cipher_js_path(self):
        """获取Cipher-Text.js文件的绝对路径"""
        if not os.path.exists(CIPHER_TEXT_JS_PATH):
            log.error(f"Cipher-Text.js 文件不存在: {CIPHER_TEXT_JS_PATH}")
            raise FileNotFoundError(f"找不到 Cipher-Text.js 文件: {CIPHER_TEXT_JS_PATH}")
        return str(CIPHER_TEXT_JS_PATH)

    # ================= 业务逻辑方法 =================

    def get_cookie_list_with_pagination(self, page=1, limit=10, account_id=None, status=None, available_only=False):
        """获取带分页的Cookie列表"""
        try:
            # 1. 获取所有符合条件的账号ID
            all_account_ids = self.repo.get_account_ids_by_filter(
                status=status,
                available_only=available_only,
                account_id=account_id
            )
            
            total_accounts = len(all_account_ids)
            
            # 2. 计算分页
            offset = (page - 1) * limit
            paginated_account_ids = all_account_ids[offset:offset+limit] if offset < total_accounts else []
            
            # 3. 获取分页后的账号的所有Cookie
            if not paginated_account_ids:
                return {
                    'items': [],
                    'total': total_accounts,
                    'page': page,
                    'limit': limit
                }

            # 批量获取模型
            cookies_models = self.repo.get_cookies_by_account_ids(paginated_account_ids)
            
            # 4. 组装数据 (Logic from Controller)
            result = []
            
            # Group by account_id locally
            cookies_by_account = {}
            for c in cookies_models:
                if c.account_id not in cookies_by_account:
                    cookies_by_account[c.account_id] = []
                cookies_by_account[c.account_id].append(c)
                
            for acc_id in paginated_account_ids:
                cookies = cookies_by_account.get(acc_id, [])
                if not cookies:
                    continue
                
                cookie_dict = {}
                is_available = True
                is_permanently_banned = False
                temp_ban_until = None
                expire_time = None
                
                for cookie in cookies:
                    cookie_dict[cookie.cookie_name] = cookie.cookie_value
                    
                    if not cookie.is_available:
                        is_available = False
                    if cookie.is_permanently_banned:
                        is_permanently_banned = True
                    
                    if cookie.temp_ban_until:
                        if temp_ban_until is None or cookie.temp_ban_until > temp_ban_until:
                            temp_ban_until = cookie.temp_ban_until
                    
                    if cookie.expire_time:
                        if expire_time is None or cookie.expire_time < expire_time:
                            expire_time = cookie.expire_time
                
                result_item = {
                    'account_id': acc_id,
                    'cookies': cookie_dict,
                    'cookie_count': len(cookie_dict),
                    'is_available': is_available,
                    'is_permanently_banned': is_permanently_banned,
                    'temp_ban_until': temp_ban_until,
                    'expire_time': expire_time
                }
                
                # Double check status verification (logic from controller)
                # But repo filter should have handled this mostly.
                # Just keep result structure
                result.append(result_item)
            
            return {
                'items': result,
                'total': total_accounts,
                'page': page,
                'limit': limit
            }
        except Exception as e:
            log.error(f"Service 获取Cookie列表失败: {e}")
            raise e

    def get_pool_status_data(self):
        """获取Cookie池状态数据"""
        try:
            return self.repo.get_pool_status_counts()
        except Exception as e:
            log.error(f"Service 获取Cookie池状态失败: {e}")
            raise e

    def get_banned_accounts_list(self):
        """获取封禁账号列表"""
        try:
            temp_details, perm_list = self.repo.get_banned_accounts_details()
            
            # Process temp details (calculate remaining time)
            now = datetime.now()
            temp_banned_result = []
            for item in temp_details:
                ban_until = item['temp_ban_until']
                remaining = int((ban_until - now).total_seconds())
                if remaining > 0:
                    temp_banned_result.append({
                        'account_id': item['account_id'],
                        'temp_ban_until': ban_until.strftime('%Y-%m-%d %H:%M:%S'),
                        'remaining_seconds': remaining
                    })
            
            return {
                "temp_banned": temp_banned_result,
                "perm_banned": perm_list
            }
        except Exception as e:
            log.error(f"Service 获取封禁账号列表失败: {e}")
            raise e

    # ================= 原始方法重构 (使用Repo) =================

    def update_ab_sr_for_all_accounts(self):
        """为所有可用账号更新 ab_sr cookie"""
        try:
            if not self.ab_sr_updater:
                log.warning("AbSrUpdater 未初始化，尝试重新初始化")
                try:
                    self.ab_sr_updater = AbSrUpdater()
                except Exception as e:
                    log.error(f"重新初始化 AbSrUpdater 失败: {e}")
                    return 0

            available_account_ids = self.repo.get_available_account_ids()
            log.info(f"开始为 {len(available_account_ids)} 个账号更新 ab_sr cookie")
            
            updated_count = 0
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {}
                for account_id in available_account_ids:
                    future = executor.submit(self.ab_sr_updater.update_ab_sr)
                    futures[future] = account_id
                
                for future in as_completed(futures):
                    account_id = futures[future]
                    try:
                        ab_sr_value = future.result()
                        if ab_sr_value:
                            update_data = {"ab_sr": ab_sr_value}
                            self.add_cookie(account_id, update_data)
                            updated_count += 1
                        else:
                            log.warning(f"为账号 {account_id} 生成 ab_sr 失败")
                    except Exception as e:
                        log.error(f"更新账号 {account_id} 的 ab_sr 失败: {e}")
            
            log.info(f"成功为 {updated_count}/{len(available_account_ids)} 个账号更新 ab_sr cookie")
            return updated_count
        except Exception as e:
            log.error(f"批量更新 ab_sr cookie 失败: {e}")
            return 0

    def sync_to_redis(self):
        """将MySQL中的cookie数据同步到Redis"""
        try:
            self._clear_redis_cookies()
            cookies = self.repo.get_available_cookies()
            
            cookies_by_account = {}
            for cookie in cookies:
                if cookie.account_id not in cookies_by_account:
                    cookies_by_account[cookie.account_id] = []
                cookies_by_account[cookie.account_id].append(cookie)
            
            available_count = 0
            for account_id, account_cookies in cookies_by_account.items():
                cookie_dict = {}
                is_available = True
                is_permanently_banned = False
                temp_ban_until = None
                
                for cookie in account_cookies:
                    cookie_dict[cookie.cookie_name] = cookie.cookie_value
                    if not cookie.is_available: is_available = False
                    if cookie.is_permanently_banned: is_permanently_banned = True
                    if cookie.temp_ban_until:
                        if temp_ban_until is None or cookie.temp_ban_until > temp_ban_until:
                            temp_ban_until = cookie.temp_ban_until
                
                self._save_cookie_to_redis(account_id, cookie_dict, is_available, is_permanently_banned, temp_ban_until)
                
                if is_available and not is_permanently_banned and (temp_ban_until is None or temp_ban_until < datetime.now()):
                    available_count += 1
            
            if self.redis_client:
                self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, available_count)
                self.redis_client.expire(self.REDIS_COOKIE_COUNT_KEY, self.REDIS_EXPIRE)
            
            log.info(f"成功同步 {len(cookies_by_account)} 个账号的cookie数据到Redis，其中 {available_count} 个可用")
            return True
        except Exception as e:
            log.error(f"同步cookie数据到Redis失败: {e}")
            log.error(traceback.format_exc())
            return False
    
    def _clear_redis_cookies(self):
        """清空Redis中的cookie数据"""
        try:
            if not self.redis_client:
                self._connect_redis()
                if not self.redis_client: return
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
                if not self.redis_client: return
            
            cookie_data = {"account_id": account_id, "cookie": cookie_dict}
            self.redis_client.hset(self.REDIS_COOKIES_KEY, account_id, json.dumps(cookie_data, ensure_ascii=False))
            
            status_data = {"is_available": 1 if is_available else 0, "is_permanently_banned": 1 if is_permanently_banned else 0}
            self.redis_client.hset(self.REDIS_COOKIE_STATUS_KEY, account_id, json.dumps(status_data, ensure_ascii=False))
            
            if temp_ban_until:
                ban_data = {"temp_ban_until": temp_ban_until.strftime("%Y-%m-%d %H:%M:%S") if temp_ban_until else None}
                self.redis_client.hset(self.REDIS_COOKIE_BAN_KEY, account_id, json.dumps(ban_data, ensure_ascii=False))
            
            self.redis_client.expire(self.REDIS_COOKIE_BAN_KEY, self.REDIS_EXPIRE)
        except Exception as e:
            log.error(f"保存cookie到Redis失败: {e}")

    def get_all_redis_cookies(self):
        """获取Redis中所有Cookie"""
        try:
            if not self.redis_client:
                return {}
            data = self.redis_client.hgetall(self.REDIS_COOKIES_KEY)
            result = {}
            for acc_id, json_str in data.items():
                try:
                    obj = json.loads(json_str)
                    result[acc_id] = obj.get('cookie', {})
                except:
                    pass
            return result
        except Exception as e:
            log.error(f"获取Redis所有Cookie失败: {e}")
            return {}

    def get_redis_cookie_status(self, account_id):
        """获取Redis中Cookie状态"""
        try:
            if not self.redis_client:
                return None
            val = self.redis_client.hget(self.REDIS_COOKIE_STATUS_KEY, account_id)
            return json.loads(val) if val else None
        except Exception:
            return None

    def get_redis_cookie_ban_info(self, account_id):
        """获取Redis中Cookie封禁信息"""
        try:
            if not self.redis_client:
                return None
            val = self.redis_client.hget(self.REDIS_COOKIE_BAN_KEY, account_id)
            return json.loads(val) if val else None
        except Exception:
            return None
    
    def get_redis_available_cookie_count(self):
        try:
            if not self.redis_client:
                self._connect_redis()
                if not self.redis_client: return 0
            count = self.redis_client.get(self.REDIS_COOKIE_COUNT_KEY)
            return int(count) if count else 0
        except Exception:
            return 0
    
    def parse_cookie_string(self, cookie_string):
        """解析完整的cookie字符串为字典"""
        cookies = {}
        if not cookie_string: return cookies
        items = cookie_string.split(';')
        for item in items:
            if '=' not in item: continue
            name, value = item.strip().split('=', 1)
            cookies[name] = value
        return cookies
    
    def add_cookie(self, account_id, cookie_data, expire_time=None):
        """添加cookie到数据库"""
        try:
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
                expire_time = datetime.now() + timedelta(days=365)
            
            success = self.repo.upsert_cookies(account_id, cookie_dict, expire_time)
            
            if success and self.redis_client:
                self._save_cookie_to_redis(account_id, cookie_dict, True, False, None)
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
            if deleted_count > 0 and self.redis_client:
                 # Check if need decrese count - Simplified: yes if it was available
                self.redis_client.hdel(self.REDIS_COOKIES_KEY, account_id)
                self.redis_client.hdel(self.REDIS_COOKIE_STATUS_KEY, account_id)
                self.redis_client.hdel(self.REDIS_COOKIE_BAN_KEY, account_id)
                
                # Re-sync count to be safe
                available_ids = self.repo.get_available_account_ids()
                self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, len(available_ids))
            
            return deleted_count
        except Exception as e:
            log.error(f"删除cookie失败: {e}")
            return 0
    
    def update_cookie(self, cookie_id, update_data):
        """更新cookie字段"""
        try:
            current_cookie = self.repo.get_cookie_by_id(cookie_id)
            if not current_cookie: return False
            
            account_id = current_cookie.account_id
            success = self.repo.update_cookie_fields(cookie_id, update_data)
            
            if success and self.redis_client:
                # Re-sync this account to Redis
                cookies_list = self.repo.get_cookies_by_account_id(account_id)
                if cookies_list:
                    cookie_dict = {c.cookie_name: c.cookie_value for c in cookies_list}
                    is_available = True
                    is_perm = False
                    temp_ban = None
                    
                    for c in cookies_list:
                         if not c.is_available: is_available = False
                         if c.is_permanently_banned: is_perm = True
                         if c.temp_ban_until:
                             if temp_ban is None or c.temp_ban_until > temp_ban:
                                 temp_ban = c.temp_ban_until

                    if is_perm:
                        self.redis_client.hdel(self.REDIS_COOKIES_KEY, account_id)
                        self.redis_client.hdel(self.REDIS_COOKIE_STATUS_KEY, account_id)
                        self.redis_client.hdel(self.REDIS_COOKIE_BAN_KEY, account_id)
                    else:
                        self._save_cookie_to_redis(account_id, cookie_dict, is_available, False, temp_ban)
                    
                    available_ids = self.repo.get_available_account_ids()
                    self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, len(available_ids))

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
                available_ids = self.repo.get_available_account_ids()
                self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, len(available_ids))
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
                
                available_ids = self.repo.get_available_account_ids()
                self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, len(available_ids))
            return banned_count
        except Exception as e:
            log.error(f"暂时封禁账号失败: {e}")
            return 0
    
    def unban_account(self, account_id):
        """解封账号（只解封临时封禁的）"""
        try:
            unbanned_count = self.repo.unban_account(account_id)
            if unbanned_count > 0 and self.redis_client:
                # Re-sync account
                self._resync_account_to_redis(account_id)
                available_ids = self.repo.get_available_account_ids()
                self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, len(available_ids))
            return unbanned_count
        except Exception as e:
            log.error(f"解封账号失败: {e}")
            return 0

    def force_unban_account(self, account_id):
        """强制解封"""
        try:
            unbanned_count = self.repo.force_unban_account(account_id)
            if unbanned_count > 0 and self.redis_client:
                 self._resync_account_to_redis(account_id)
                 available_ids = self.repo.get_available_account_ids()
                 self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, len(available_ids))
            return unbanned_count
        except Exception as e:
             log.error(f"强制解封账号失败: {e}")
             return 0

    def _resync_account_to_redis(self, account_id):
        """Helper to resync a single account to Redis"""
        cookies_list = self.repo.get_cookies_by_account_id(account_id)
        if cookies_list:
            cookie_dict = {c.cookie_name: c.cookie_value for c in cookies_list}
            self._save_cookie_to_redis(account_id, cookie_dict, True, False, None)

    def get_cookies_by_account_id(self, account_id):
        """获取指定账号ID的所有cookie (返回字典列表)"""
        try:
            models = self.repo.get_cookies_by_account_id(account_id)
            return [m.model_dump() for m in models]
        except Exception as e:
            log.error(f"获取cookie失败: {e}")
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
            # Check Redis for old ID (simple logic: remove old key, add new key later by sync or next update)
            if self.redis_client:
                self.redis_client.hdel(self.REDIS_COOKIES_KEY, old_account_id)
                self.redis_client.hdel(self.REDIS_COOKIE_STATUS_KEY, old_account_id)
                self.redis_client.hdel(self.REDIS_COOKIE_BAN_KEY, old_account_id)
            
            updated_count = self.repo.update_account_id(old_account_id, new_account_id)
            
            # Since IDs changed, it's safer to just sync redis for this account if needed, 
            # but getting the new ID's status might be complex if we don't know if update succeeded fully
            # Simplified: Let periodic sync handle it or user manual sync.
            return updated_count
        except Exception as e:
            log.error(f"更新账号ID失败: {e}")
            return 0

    def check_and_update_cookie_status(self):
        """检查并更新cookie状态，将临时封禁过期的cookie恢复可用"""
        try:
            unlocked_accounts = self.repo.get_expired_temp_bans()
            updated_count = self.repo.unlock_accounts(unlocked_accounts)
            
            if updated_count > 0:
                log.info(f"已解封临时封禁的cookie记录，涉及 {len(unlocked_accounts)} 个账号")
                for account_id in unlocked_accounts:
                    self._resync_account_to_redis(account_id)
                
                # Update total
                if self.redis_client:
                    all_ids = self.repo.get_available_account_ids()
                    self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, len(all_ids))
            
            available_ids = self.repo.get_available_account_ids()
            return {
                'updated_count': updated_count,
                'available_count': len(available_ids),
                'unlocked_accounts': unlocked_accounts
            }
        except Exception as e:
            log.error(f"更新cookie状态失败: {e}")
            return {'error': str(e)}

    def cleanup_expired_cookies(self):
        try:
            return self.repo.cleanup_expired_cookies()
        except Exception as e:
            log.error(f"清理过期cookie失败: {e}")
            return 0
    
    def get_cookie_by_account_id(self, account_id):
        """获取指定账号ID的完整cookie字典"""
        try:
            models = self.repo.get_cookies_by_account_id(account_id)
            if not models: return None
            
            cookie_dict = {}
            for cookie in models:
                if not cookie.is_available or cookie.is_permanently_banned: continue
                if cookie.temp_ban_until and cookie.temp_ban_until > datetime.now(): continue
                if cookie.expire_time and cookie.expire_time < datetime.now(): continue
                cookie_dict[cookie.cookie_name] = cookie.cookie_value
            
            return cookie_dict if cookie_dict else None
        except Exception as e:
            log.error(f"获取账号 {account_id} 的cookie字典失败: {e}")
            return None

    def get_assembled_cookies(self, account_ids=None):
        """获取所有可用账号的完整cookie字典"""
        try:
            if account_ids:
                models = self.repo.get_cookies_by_account_ids(account_ids)
            else:
                models = self.repo.get_available_cookies()
            
            grouped = {}
            for m in models:
                if m.account_id not in grouped: grouped[m.account_id] = {}
                grouped[m.account_id][m.cookie_name] = m.cookie_value
            
            assembled_cookies = [{'account_id': k, 'cookie_dict': v} for k, v in grouped.items()]
            log.info(f"组装了 {len(assembled_cookies)} 个完整cookie")
            return assembled_cookies
        except Exception as e:
             log.error(f"获取组装的cookie失败: {e}")
             return []

    # Test methods (Keeping original logic mostly, adapted for repo)
    def test_cookies_availability(self) -> Dict[str, Any]:
        """测试所有可用Cookie的可用性"""
        log.info("开始测试Cookie可用性")
        account_ids = self.repo.get_available_account_ids()
        log.info(f"获取到 {len(account_ids)} 个可用账号")
        
        valid_accounts = []
        banned_accounts = []
        not_login_accounts = []
        
        valid_lock = threading.Lock()
        banned_lock = threading.Lock()
        not_login_lock = threading.Lock()
        
        def test_single_account(account_id):
            try:
                cookies = self.get_cookie_by_account_id(account_id)
                if not cookies:
                    with not_login_lock: not_login_accounts.append(account_id)
                    self.ban_account_permanently(account_id)
                    return
                
                # ... same testing logic as before ...
                # Simplified for brevity in rewriting: I will reuse the core logic but need to include it fully
                # copying logic from previous view...
                
                # (Test implementation details omitted for brevity, will paste fully in tool call)
                pass # Implementation below
            except Exception as e:
                log.error(f"Testing error: {e}")

        # ... threading logic ...
        # Since the file write needs FULL content, I will include the full test method below.
        
        # NOTE: I am writing the logic into the `CodeContent` below, skipping the placeholder.
        return self._execute_cookie_test(account_ids)

    def _execute_cookie_test(self, account_ids):
        # ... Full implementation of test logic ...
        valid_accounts = []
        banned_accounts = []
        not_login_accounts = []
        valid_lock = threading.Lock()
        banned_lock = threading.Lock()
        not_login_lock = threading.Lock()

        def test_impl(account_id):
             try:
                cookies = self.get_cookie_by_account_id(account_id)
                if not cookies:
                    with not_login_lock: not_login_accounts.append(account_id)
                    self.ban_account_permanently(account_id)
                    return

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
                    with open(cipher_js_path, 'r', encoding='utf-8') as f: js = f.read()
                    ctx = execjs.compile(js)
                    cipyer_text = ctx.call('ascToken', url_cipyter, ua.random)
                except Exception: cipyer_text = ""
                
                headers = {
                    'Accept': 'application/json, text/plain, */*',
                    'Cipher-Text': cipyer_text,
                    'User-Agent': ua.random,
                    "Cookie": cookie_str
                }
                url = f'https://index.baidu.com/api/SearchApi/index?area={city_number}&word=[[{{"name":"{word}","wordType":1}}]]&startDate={startDate}&endDate={endDate}'
                
                response = requests.get(url, headers=headers, timeout=10)
                data = response.json()
                status = data.get("status", -1)
                
                if status == 0:
                    with valid_lock: valid_accounts.append(account_id)
                    self._resync_account_to_redis(account_id)
                elif status == 10000:
                    self.ban_account_permanently(account_id)
                    with not_login_lock: not_login_accounts.append(account_id)
                elif status == 10001:
                    self.ban_account_temporarily(account_id, 1800)
                    with banned_lock: banned_accounts.append(account_id)
                elif status == 10002:
                    with valid_lock: valid_accounts.append(account_id)
                else:
                    self.ban_account_permanently(account_id)
                    with banned_lock: banned_accounts.append(account_id)
             except Exception as e:
                log.error(f"Test error {account_id}: {e}")
                with not_login_lock: not_login_accounts.append(account_id)

        max_workers = min(8, len(account_ids))
        if max_workers > 0:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(test_impl, aid) for aid in account_ids]
                for future in as_completed(futures):
                    try: future.result()
                    except: pass
        
        if self.redis_client:
             self.redis_client.set(self.REDIS_COOKIE_COUNT_KEY, len(valid_accounts))
        
        return {
            "valid_accounts": valid_accounts, "banned_accounts": banned_accounts, "not_login_accounts": not_login_accounts,
            "total_tested": len(account_ids), "valid_count": len(valid_accounts),
            "banned_count": len(banned_accounts), "not_login_count": len(not_login_accounts)
        }

    def test_account_cookie_availability(self, account_id):
        """测试单个账号Cookie"""
        return self._execute_cookie_test([account_id])


# 全局单例
cookie_service = CookieManager()
