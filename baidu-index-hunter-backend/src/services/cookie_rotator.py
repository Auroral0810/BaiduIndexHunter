"""
Cookie轮换管理模块，负责获取、验证和轮换Cookie
"""
import time
import random
import json
import threading
from datetime import datetime, timedelta, date
from src.core.logger import log
# from src.data.repositories.mysql_manager import mysql_manager # Removed
from src.data.repositories.cookie_usage_repository import cookie_usage_repo
from src.core.config import COOKIE_CONFIG
from src.services.cookie_service import CookieManager


class CookieRotator:
    def __init__(self):
        self.cookie_list = []
        self.cookie_index = 0
        self.cookie_lock = threading.Lock()
        self.cookie_update_interval = 300  # 5分钟
        self.cookie_update_lock = threading.Lock()
        self.last_update_time = 0
        self.cookie_manager = CookieManager()
        self.load_balancing_strategy = COOKIE_CONFIG.get('load_balancing_strategy', 'least_recently_used')  # 默认使用LRU策略
        # Redis键名 - 添加cookie使用量相关的键
        self.REDIS_COOKIE_USAGE_KEY = "baidu_index:cookie_usage"
        self.REDIS_COOKIE_USAGE_DATE_KEY = "baidu_index:cookie_usage_date"
        
        self.usage_repo = cookie_usage_repo

        # 同步Redis和MySQL中的使用量数据
        self._sync_usage_data()
        self._update_cookie_list()
    
    def _sync_usage_data(self):
        """同步Redis和MySQL中的Cookie使用量数据"""
        try:
            # 检查Redis客户端是否可用
            if not self.cookie_manager.redis_client:
                log.warning("Redis客户端不可用，无法同步使用量数据")
                return
            
            # 获取当前日期
            today_str = datetime.now().strftime('%Y-%m-%d')
            today_date = datetime.now().date()
            
            # 从MySQL获取今日的使用量数据 (使用 Repository)
            mysql_data = self.usage_repo.get_usage_by_date(today_date)
            
            # 从Redis获取今日的使用量数据
            redis_key = f"{self.REDIS_COOKIE_USAGE_KEY}:{today_str}"
            redis_data = self.cookie_manager.redis_client.hgetall(redis_key)
            
            # 将MySQL数据转换为字典格式
            mysql_dict = {item.account_id: item.usage_count for item in mysql_data}
            
            # 将Redis数据转换为字典格式
            redis_dict = {account_id: int(count) for account_id, count in redis_data.items()}
            
            # 合并数据，取两者中的最大值
            merged_data = {}
            all_account_ids = set(mysql_dict.keys()) | set(redis_dict.keys())
            
            for account_id in all_account_ids:
                mysql_count = mysql_dict.get(account_id, 0)
                redis_count = redis_dict.get(account_id, 0)
                merged_data[account_id] = max(mysql_count, redis_count)
            
            # 更新Redis数据
            pipe = self.cookie_manager.redis_client.pipeline()
            pipe.delete(redis_key)  # 先删除旧数据
            
            if merged_data:
                for account_id, count in merged_data.items():
                    pipe.hset(redis_key, account_id, count)
                pipe.expire(redis_key, 60*60*24*30)  # 设置30天过期时间
            
            pipe.execute()
            
            # 更新MySQL数据 (使用 Repository)
            for account_id, count in merged_data.items():
                self.usage_repo.update_usage(account_id, today_date, count)
            
            log.info(f"已同步{len(merged_data)}个账号的使用量数据")
            
        except Exception as e:
            log.error(f"同步使用量数据失败: {e}")
    
    def _update_cookie_list(self):
        """更新可用Cookie列表"""
        with self.cookie_update_lock:
            current_time = time.time()
            # 如果距离上次更新时间不足更新间隔，则跳过
            if current_time - self.last_update_time < self.cookie_update_interval:
                return
            
            try:
                # 从Redis获取所有可用的Cookie
                available_cookies = self.cookie_manager.get_all_redis_cookies()
                
                if not available_cookies:
                    log.warning("没有可用的Cookie")
                    return
                
                # 获取今日的cookie使用情况
                today = datetime.now().strftime('%Y-%m-%d')
                usage_data = {}
                if self.cookie_manager.redis_client:
                    usage_data = self.cookie_manager.redis_client.hgetall(f"{self.REDIS_COOKIE_USAGE_KEY}:{today}")
                
                # 转换为列表格式
                cookie_list = []
                for account_id, cookie_dict in available_cookies.items():
                    # 检查Cookie状态
                    status = self.cookie_manager.get_redis_cookie_status(account_id)
                    if not status or status.get('is_available') != 1:
                        continue
                    
                    # 检查是否被临时封禁
                    ban_info = self.cookie_manager.get_redis_cookie_ban_info(account_id)
                    if ban_info:
                        temp_ban_until = ban_info.get('temp_ban_until')
                        if temp_ban_until:
                            ban_time = datetime.strptime(temp_ban_until, "%Y-%m-%d %H:%M:%S")
                            if ban_time > datetime.now():
                                continue
                    
                    # 获取今日使用次数
                    use_count = int(usage_data.get(account_id, 0))
                    
                    # 计算最后使用时间，如果今日未使用则设置为0
                    last_use_time = 0
                    if use_count > 0:
                        # 如果有使用记录，设置一个基于使用次数的时间戳
                        # 使用次数越多，时间戳越大（越近）
                        last_use_time = current_time - (1000000 / (use_count + 1))
                    
                    cookie_list.append({
                        'account_id': account_id,
                        'cookie': cookie_dict,
                        'use_count': use_count,
                        'last_use_time': last_use_time
                    })
                
                # 更新Cookie列表
                with self.cookie_lock:
                    self.cookie_list = cookie_list
                    self.cookie_index = 0
                
                self.last_update_time = current_time
                log.info(f"已更新Cookie列表，共 {len(cookie_list)} 个可用Cookie")
            
            except Exception as e:
                log.error(f"更新Cookie列表失败: {e}")
    
    def reset_cache(self):
        """重置Cookie缓存，强制下次获取时重新从Redis加载"""
        with self.cookie_lock:
            self.cookie_list = []
            self.cookie_index = 0
            self.last_update_time = 0
            log.info("已重置Cookie缓存，下次获取将重新加载")
        return True
    
    def get_cookie(self):
        """获取一个可用的Cookie（兼容性方法）
        
        Returns:
            tuple: (account_id, cookie_dict) 元组，与爬虫代码期望的格式匹配
        """
        cookie_info = self.get_available_cookie()
        if cookie_info:
            return cookie_info['account_id'], cookie_info['cookie']
        return None, None
    
    def _record_cookie_usage(self, account_id):
        """记录cookie使用量"""
        try:
            today_str = datetime.now().strftime('%Y-%m-%d')
            today_date = datetime.now().date()
            
            # 更新Redis中的使用量
            if self.cookie_manager.redis_client:
                redis_key = f"{self.REDIS_COOKIE_USAGE_KEY}:{today_str}"
                self.cookie_manager.redis_client.hincrby(redis_key, account_id, 1)
                self.cookie_manager.redis_client.expire(redis_key, 60*60*24*30)
            
            # 异步更新MySQL数据库 (使用 Repository)
            threading.Thread(target=self._update_db_cookie_usage, args=(account_id, today_date)).start()
            
        except Exception as e:
            log.error(f"记录cookie使用量失败: {e}")
    
    def _update_db_cookie_usage(self, account_id, usage_date):
        """更新数据库中的cookie使用量 (异步调用)"""
        try:
            # 使用 Repository 增加使用量
            self.usage_repo.increment_usage(account_id, usage_date)
        except Exception as e:
            log.error(f"更新数据库cookie使用量失败: {e}")
    
    def get_cookie_usage(self, account_id=None, start_date=None, end_date=None):
        """获取cookie使用量统计"""
        try:
            # 日期字符串转换为 date 对象
            start_d = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            end_d = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
            
            # 使用 Repository 获取统计
            results = self.usage_repo.get_usage_stats(
                account_id=account_id,
                start_date=start_d,
                end_date=end_d
            )
            
            # 转换为字典列表以保持兼容性
            return [
                {
                    "account_id": r.account_id,
                    "usage_date": r.usage_date.strftime('%Y-%m-%d') if isinstance(r.usage_date, (date, datetime)) else str(r.usage_date),
                    "usage_count": r.usage_count
                }
                for r in results
            ]
        except Exception as e:
            log.error(f"获取cookie使用量统计失败: {e}")
            return []
    
    def get_today_usage_from_redis(self):
        """从Redis获取今日的cookie使用量"""
        try:
            if not self.cookie_manager.redis_client:
                return {}
            
            today = datetime.now().strftime('%Y-%m-%d')
            usage_data = self.cookie_manager.redis_client.hgetall(f"{self.REDIS_COOKIE_USAGE_KEY}:{today}")
            
            # 转换为整数
            result = {}
            for account_id, count in usage_data.items():
                result[account_id] = int(count)
            
            return result
        except Exception as e:
            log.error(f"从Redis获取今日cookie使用量失败: {e}")
            return {}
    
    def get_available_cookie(self):
        """获取一个可用的Cookie"""
        # 如果Cookie列表为空或者需要更新，则更新列表
        if not self.cookie_list or time.time() - self.last_update_time >= self.cookie_update_interval:
            self._update_cookie_list()
        
        # 如果仍然没有可用Cookie，返回None
        if not self.cookie_list:
            log.warning("没有可用的Cookie")
            return None
        
        with self.cookie_lock:
            # 根据不同的负载均衡策略选择Cookie
            if self.load_balancing_strategy == 'random':
                cookie_info = random.choice(self.cookie_list)
            elif self.load_balancing_strategy == 'least_used':
                cookie_info = min(self.cookie_list, key=lambda x: x['use_count'])
            elif self.load_balancing_strategy == 'least_recently_used':
                cookie_info = min(self.cookie_list, key=lambda x: x['last_use_time'] or 0)
            else:
                cookie_info = self.cookie_list[self.cookie_index]
                self.cookie_index = (self.cookie_index + 1) % len(self.cookie_list)
            
            # 更新使用计数和时间
            cookie_info['use_count'] += 1
            cookie_info['last_use_time'] = time.time()
            
            # 记录cookie使用量
            self._record_cookie_usage(cookie_info['account_id'])
            
            return {
                'account_id': cookie_info['account_id'],
                'cookie': cookie_info['cookie'],
                'cookie_id': cookie_info['account_id']
            }
    
    def report_cookie_status(self, account_id, is_valid, permanent=False):
        """报告Cookie状态，用于与爬虫代码兼容"""
        if is_valid:
            return self.mark_cookie_valid(account_id)
        elif permanent:
            # 永久封禁
            try:
                self.cookie_manager.ban_account_permanently(account_id)
                log.warning(f"Cookie {account_id} 已被标记为永久无效")
                
                # 从当前列表中移除
                with self.cookie_lock:
                    self.cookie_list = [c for c in self.cookie_list if c['account_id'] != account_id]
                    if self.cookie_list:
                        self.cookie_index = self.cookie_index % len(self.cookie_list)
                    else:
                        self.cookie_index = 0
                
                return True
            except Exception as e:
                log.error(f"标记Cookie为永久无效失败: {e}")
                return False
        else:
            return self.mark_cookie_invalid(account_id)
    
    def mark_cookie_invalid(self, cookie_id):
        """标记Cookie为无效"""
        try:
            # 临时禁用Cookie，使用配置的冷却时间
            cooldown_time = COOKIE_CONFIG.get('block_cooldown', 1800)
            self.cookie_manager.ban_account_temporarily(cookie_id, cooldown_time)
            log.warning(f"Cookie {cookie_id} 已被标记为无效，临时禁用{cooldown_time//60}分钟")
            
            # 从当前列表中移除
            with self.cookie_lock:
                self.cookie_list = [c for c in self.cookie_list if c['account_id'] != cookie_id]
                if self.cookie_list:
                    self.cookie_index = self.cookie_index % len(self.cookie_list)
                else:
                    self.cookie_index = 0
            
            return True
        except Exception as e:
            log.error(f"标记Cookie为无效失败: {e}")
            return False
    
    def mark_cookie_valid(self, cookie_id):
        """标记Cookie为有效"""
        return True
    
    def set_load_balancing_strategy(self, strategy):
        """设置负载均衡策略"""
        valid_strategies = ['round_robin', 'random', 'least_used', 'least_recently_used']
        if strategy in valid_strategies:
            self.load_balancing_strategy = strategy
            log.info(f"已设置Cookie负载均衡策略为: {strategy}")
            return True
        else:
            log.warning(f"无效的负载均衡策略: {strategy}，有效选项: {', '.join(valid_strategies)}")
            return False
    
    def get_cookie_stats(self):
        """获取Cookie使用统计信息"""
        with self.cookie_lock:
            stats = {
                'total_cookies': len(self.cookie_list),
                'strategy': self.load_balancing_strategy,
                'cookies': [{
                    'account_id': c['account_id'],
                    'use_count': c['use_count'],
                    'last_use_time': datetime.fromtimestamp(c['last_use_time']).strftime('%Y-%m-%d %H:%M:%S') if c['last_use_time'] else None
                } for c in self.cookie_list]
            }
            return stats
    
    def close(self):
        """关闭资源"""
        if hasattr(self, 'cookie_manager'):
            self.cookie_manager.close()


# 创建Cookie轮换器单例
cookie_rotator = CookieRotator()
        