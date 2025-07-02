"""
Cookie轮换管理模块，负责获取、验证和轮换Cookie
"""
import time
import random
import json
import threading
from datetime import datetime, timedelta
from utils.logger import log
from db.mysql_manager import mysql_manager
from config.settings import COOKIE_CONFIG
from cookie_manager.cookie_manager import CookieManager


class CookieRotator:
    def __init__(self):
        self.cookie_list = []
        self.cookie_index = 0
        self.cookie_lock = threading.Lock()
        self.cookie_update_interval = 300  # 5分钟
        self.cookie_update_lock = threading.Lock()
        self.last_update_time = 0
        self.cookie_manager = CookieManager()
        self.load_balancing_strategy = COOKIE_CONFIG.get('load_balancing_strategy', 'round_robin')
        self._update_cookie_list()
    
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
                    
                    cookie_list.append({
                        'account_id': account_id,
                        'cookie': cookie_dict,
                        'use_count': 0,
                        'last_use_time': 0
                    })
                
                # 更新Cookie列表
                with self.cookie_lock:
                    self.cookie_list = cookie_list
                    self.cookie_index = 0
                
                self.last_update_time = current_time
                log.info(f"已更新Cookie列表，共 {len(cookie_list)} 个可用Cookie")
            
            except Exception as e:
                log.error(f"更新Cookie列表失败: {e}")
    
    def get_cookie(self):
        """获取一个可用的Cookie（兼容性方法）
        
        Returns:
            tuple: (account_id, cookie_dict) 元组，与爬虫代码期望的格式匹配
        """
        cookie_info = self.get_available_cookie()
        if cookie_info:
            return cookie_info['account_id'], cookie_info['cookie']
        return None, None
    
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
                # 随机选择策略
                cookie_info = random.choice(self.cookie_list)
            elif self.load_balancing_strategy == 'least_used':
                # 最少使用策略
                cookie_info = min(self.cookie_list, key=lambda x: x['use_count'])
            elif self.load_balancing_strategy == 'least_recently_used':
                # 最近最少使用策略
                cookie_info = min(self.cookie_list, key=lambda x: x['last_use_time'] or 0)
            else:
                # 默认轮询策略
                cookie_info = self.cookie_list[self.cookie_index]
                # 更新索引，循环使用
                self.cookie_index = (self.cookie_index + 1) % len(self.cookie_list)
            
            # 更新使用计数和时间
            cookie_info['use_count'] += 1
            cookie_info['last_use_time'] = time.time()
            
            return {
                'account_id': cookie_info['account_id'],
                'cookie': cookie_info['cookie'],
                'cookie_id': cookie_info['account_id']  # 使用account_id作为cookie_id
            }
    
    def report_cookie_status(self, account_id, is_valid, permanent=False):
        """报告Cookie状态，用于与爬虫代码兼容
        
        Args:
            account_id (str): Cookie账号ID
            is_valid (bool): Cookie是否有效
            permanent (bool): 是否永久封禁
        
        Returns:
            bool: 操作是否成功
        """
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
        # 对于有效的Cookie，不需要特殊处理
        return True
    
    def set_load_balancing_strategy(self, strategy):
        """设置负载均衡策略
        
        策略选项:
        - round_robin: 轮询策略（默认）
        - random: 随机选择策略
        - least_used: 最少使用策略
        - least_recently_used: 最近最少使用策略
        """
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
        