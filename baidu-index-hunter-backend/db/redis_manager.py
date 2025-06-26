"""
Redis缓存管理模块
"""
import json
import redis
from utils.logger import log
from config.settings import REDIS_CONFIG
from datetime import datetime


class RedisManager:
    """Redis缓存管理器，用于缓存活跃的cookie信息"""
    def __init__(self):
        self.redis_config = REDIS_CONFIG
        self.client = None
        self.connect()
        
        # 定义键前缀
        self.cookie_key_prefix = "baidu_index:cookie:"
        self.cookie_list_key = "baidu_index:cookie:list"
        self.cookie_usage_key_prefix = "baidu_index:usage:"
        self.cookie_success_key_prefix = "baidu_index:success:"
    
    def connect(self):
        """连接Redis"""
        try:
            self.client = redis.Redis(
                host=self.redis_config['host'],
                port=self.redis_config['port'],
                db=self.redis_config['db'],
                password=self.redis_config['password'],
                decode_responses=True  # 自动将字节解码为字符串
            )
            self.client.ping()  # 测试连接
            log.info(f"成功连接到Redis: {self.redis_config['host']}:{self.redis_config['port']}")
            return True
        except Exception as e:
            log.error(f"Redis连接失败: {e}")
            self.client = None
            return False
    
    def cache_cookie(self, account_id, cookie_dict):
        """
        缓存Cookie到Redis
        :param account_id: 账号ID
        :param cookie_dict: Cookie字典
        """
        try:
            # 设置Cookie缓存
            self.client.hset(f"cookie:{account_id}", mapping=cookie_dict)
            
            # 设置为可用状态
            self.client.hset("cookie_status", account_id, "available")
            
            # 记录最后更新时间
            self.client.hset("cookie_last_updated", account_id, datetime.now().isoformat())
            
            # 添加到账号ID集合
            self.client.sadd("cookie_ids", account_id)
            
            log.debug(f"Cookie {account_id} 已缓存到Redis")
        except Exception as e:
            log.error(f"缓存Cookie到Redis失败: {e}")
    
    def get_cookie(self, account_id):
        """
        从Redis获取Cookie
        :param account_id: 账号ID
        :return: Cookie字典
        """
        try:
            # 检查cookie状态
            status = self.client.hget("cookie_status", account_id)
            if status and status == "locked":
                log.debug(f"Cookie {account_id} 已被锁定，无法使用")
                return None
                
            # 获取cookie字典
            cookie_dict = self.client.hgetall(f"cookie:{account_id}")
            
            # 返回Python字典
            if cookie_dict:
                return cookie_dict
            return None
        except Exception as e:
            log.error(f"从Redis获取Cookie失败: {e}")
            return None
    
    def remove_cookie(self, account_id):
        """
        从缓存中移除cookie
        :param account_id: cookie的账号ID
        """
        key = f"{self.cookie_key_prefix}{account_id}"
        try:
            self.client.delete(key)
            self.client.srem(self.cookie_list_key, account_id)
            log.debug(f"账号 {account_id} 的Cookie已从Redis缓存移除")
            return True
        except Exception as e:
            log.error(f"从Redis移除Cookie失败: {e}")
            return False
    
    def get_all_cached_cookie_ids(self):
        """获取所有缓存的cookie账号ID列表"""
        try:
            # 使用正确的键名获取所有cookie ID
            return list(self.client.smembers("cookie_ids"))
        except Exception as e:
            log.error(f"获取缓存Cookie列表失败: {e}")
            return []
    
    def record_cookie_usage(self, account_id):
        """
        记录cookie的使用次数
        :param account_id: cookie的账号ID
        """
        key = f"{self.cookie_usage_key_prefix}{account_id}"
        try:
            self.client.incr(key)
            log.debug(f"账号 {account_id} 的Cookie使用计数+1")
        except Exception as e:
            log.error(f"记录Cookie使用次数失败: {e}")
    
    def record_cookie_success(self, account_id, is_success=True):
        """
        记录cookie请求的成功状态
        :param account_id: cookie的账号ID
        :param is_success: 是否成功
        """
        key = f"{self.cookie_success_key_prefix}{account_id}"
        try:
            if is_success:
                self.client.incr(f"{key}:success")
            else:
                self.client.incr(f"{key}:fail")
            log.debug(f"账号 {account_id} 的Cookie成功状态已记录: {is_success}")
        except Exception as e:
            log.error(f"记录Cookie成功状态失败: {e}")
    
    def get_cookie_metrics(self, account_id):
        """
        获取cookie的使用指标
        :param account_id: cookie的账号ID
        :return: 包含使用次数和成功率的字典
        """
        usage_key = f"{self.cookie_usage_key_prefix}{account_id}"
        success_key = f"{self.cookie_success_key_prefix}{account_id}:success"
        fail_key = f"{self.cookie_success_key_prefix}{account_id}:fail"
        
        try:
            usage_count = int(self.client.get(usage_key) or 0)
            success_count = int(self.client.get(success_key) or 0)
            fail_count = int(self.client.get(fail_key) or 0)
            
            total_requests = success_count + fail_count
            success_rate = 100 * success_count / total_requests if total_requests > 0 else 0
            
            return {
                "usage_count": usage_count,
                "success_count": success_count,
                "fail_count": fail_count,
                "success_rate": success_rate
            }
        except Exception as e:
            log.error(f"获取Cookie指标失败: {e}")
            return {
                "usage_count": 0,
                "success_count": 0,
                "fail_count": 0,
                "success_rate": 0
            }

    def mark_cookie_locked(self, account_id):
        """
        标记Cookie为锁定状态
        :param account_id: 账号ID
        """
        try:
            # 设置锁定状态
            self.client.hset("cookie_status", account_id, "locked")
            
            # 记录锁定时间
            self.client.hset("cookie_lock_time", account_id, datetime.now().isoformat())
            
            # log.info(f"Redis中已标记Cookie {account_id} 为锁定状态")
            return True
        except Exception as e:
            log.error(f"标记Cookie锁定状态失败: {e}")
            return False
    
    def mark_cookie_available(self, account_id):
        """
        标记Cookie为可用状态
        :param account_id: 账号ID
        """
        try:
            # 设置可用状态
            self.client.hset("cookie_status", account_id, "available")
            
            # 删除锁定时间
            self.client.hdel("cookie_lock_time", account_id)
            
            # log.info(f"Redis中已标记Cookie {account_id} 为可用状态")
            return True
        except Exception as e:
            log.error(f"标记Cookie可用状态失败: {e}")
            return False
    
    def is_cookie_locked(self, account_id):
        """
        检查Cookie是否被锁定
        :param account_id: 账号ID
        :return: 是否锁定
        """
        try:
            status = self.client.hget("cookie_status", account_id)
            return status and status == "locked"
        except Exception as e:
            log.error(f"检查Cookie锁定状态失败: {e}")
            return False
    
    def get_all_locked_cookies(self):
        """
        获取所有被锁定的Cookie账号ID
        :return: 被锁定的账号ID列表
        """
        try:
            locked_cookies = []
            all_ids = self.get_all_cached_cookie_ids()
            
            for account_id in all_ids:
                if self.is_cookie_locked(account_id):
                    locked_cookies.append(account_id)
            
            return locked_cookies
        except Exception as e:
            log.error(f"获取所有被锁定的Cookie失败: {e}")
            return []


# 创建Redis管理器单例
redis_manager = RedisManager() 