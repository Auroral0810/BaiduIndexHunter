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
from config.settings import COOKIE_BLOCK_COOLDOWN
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
            # 轮询获取下一个Cookie
            cookie_info = self.cookie_list[self.cookie_index]
            
            # 更新使用计数和时间
            cookie_info['use_count'] += 1
            cookie_info['last_use_time'] = time.time()
            
            # 更新索引，循环使用
            self.cookie_index = (self.cookie_index + 1) % len(self.cookie_list)
            
            return {
                'account_id': cookie_info['account_id'],
                'cookie': cookie_info['cookie'],
                'cookie_id': cookie_info['account_id']  # 使用account_id作为cookie_id
            }
    
    def mark_cookie_invalid(self, cookie_id):
        """标记Cookie为无效"""
        try:
            # 临时禁用Cookie 30分钟
            self.cookie_manager.ban_account_temporarily(cookie_id, 1800)
            log.warning(f"Cookie {cookie_id} 已被标记为无效，临时禁用30分钟")
            
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
    
    def close(self):
        """关闭资源"""
        if hasattr(self, 'cookie_manager'):
            self.cookie_manager.close()


# 创建Cookie轮换器单例
cookie_rotator = CookieRotator()
        