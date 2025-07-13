"""
请求频率限制模块，防止请求过于频繁导致IP被封
"""
import time
import random
import threading
from datetime import datetime
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import log
from config.settings import SPIDER_CONFIG

class RateLimiter:
    """
    请求频率限制器
    控制请求的频率，防止请求过于频繁导致IP被封
    """
    
    def __init__(self, min_interval=None, max_interval=None, default_interval=None):
        """
        初始化频率限制器
        
        参数:
            min_interval (float): 最小请求间隔时间（秒）
            max_interval (float): 最大请求间隔时间（秒）
            default_interval (float): 默认请求间隔时间（秒）
        """
        self.min_interval = min_interval or SPIDER_CONFIG.get('min_interval', 0.8)  # 减少默认间隔
        self.max_interval = max_interval or SPIDER_CONFIG.get('max_interval', 1)  # 减少默认间隔
        self.default_interval = default_interval or SPIDER_CONFIG.get('default_interval', 0.8)  # 减少默认间隔
        
        self.last_request_time = 0
        self.lock = threading.Lock()
        self.consecutive_failures = 0
        self.max_consecutive_failures = SPIDER_CONFIG.get('max_consecutive_failures', 3)
        self.failure_multiplier = SPIDER_CONFIG.get('failure_multiplier', 1.2)  # 减少失败后的等待时间倍数
        
        log.info(f"请求频率限制器初始化: 间隔 {self.min_interval}~{self.max_interval}秒")
    
    def wait(self):
        """
        等待适当的时间以满足频率限制
        
        返回:
            float: 实际等待的时间（秒）
        """
        with self.lock:
            current_time = time.time()
            
            # 计算上次请求到现在的时间间隔
            elapsed = current_time - self.last_request_time
            
            # 计算需要等待的时间
            if self.consecutive_failures > 0:
                # 如果有连续失败，增加等待时间
                wait_time = random.uniform(
                    self.min_interval * self.failure_multiplier ** min(self.consecutive_failures, self.max_consecutive_failures),
                    self.max_interval * self.failure_multiplier ** min(self.consecutive_failures, self.max_consecutive_failures)
                )
            else:
                # 正常等待时间
                wait_time = random.uniform(self.min_interval, self.max_interval)
            
            # 如果已经等待了足够长的时间，不需要额外等待
            if elapsed >= wait_time:
                actual_wait = 0
            else:
                actual_wait = wait_time - elapsed
                time.sleep(actual_wait)
            
            # 更新上次请求时间
            self.last_request_time = time.time()
            
            if actual_wait > 0:
                log.debug(f"请求频率限制: 等待 {actual_wait:.2f} 秒")
            
            return actual_wait
    
    def report_success(self):
        """报告请求成功，重置连续失败计数"""
        with self.lock:
            if self.consecutive_failures > 0:
                self.consecutive_failures = 0
                log.debug("请求成功，重置连续失败计数")
    
    def report_failure(self):
        """报告请求失败，增加连续失败计数"""
        with self.lock:
            self.consecutive_failures += 1
            log.warning(f"请求失败，连续失败次数: {self.consecutive_failures}")
            
            # 如果连续失败次数过多，增加等待时间
            if self.consecutive_failures >= self.max_consecutive_failures:
                backoff_time = self.default_interval * (self.failure_multiplier ** self.consecutive_failures)
                log.warning(f"连续失败次数过多，增加等待时间: {backoff_time:.2f} 秒")
                time.sleep(backoff_time)
    
    def reset(self):
        """重置限制器状态"""
        with self.lock:
            self.last_request_time = 0
            self.consecutive_failures = 0
            log.debug("请求频率限制器已重置")


# 创建全局实例
rate_limiter = RateLimiter()
