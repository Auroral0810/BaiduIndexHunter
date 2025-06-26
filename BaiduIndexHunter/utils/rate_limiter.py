"""
请求频率限制模块，防止请求过于频繁导致IP被封
"""
import time
import random
from utils.logger import log
from config.settings import SPIDER_CONFIG


class RateLimiter:
    """请求频率限制器，控制请求间隔"""
    
    def __init__(self, min_delay=None, max_delay=None):
        """
        初始化频率限制器
        :param min_delay: 最小延迟秒数，默认使用配置值
        :param max_delay: 最大延迟秒数，默认使用配置值
        """
        self.min_delay = min_delay or SPIDER_CONFIG['min_interval']
        self.max_delay = max_delay or SPIDER_CONFIG['max_interval']
        self.last_request_time = 0
    
    def wait(self):
        """
        等待适当时间后再发送下一个请求
        :return: 实际等待的秒数
        """
        now = time.time()
        elapsed = now - self.last_request_time
        
        # 如果是首次请求，不需要等待
        if self.last_request_time == 0:
            self.last_request_time = now
            return 0
        
        # 计算需要等待的时间
        delay = random.uniform(self.min_delay, self.max_delay)
        wait_time = max(0, delay - elapsed)
        
        if wait_time > 0:
            log.debug(f"频率限制: 等待 {wait_time:.2f} 秒")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
        return wait_time


# 创建频率限制器单例
rate_limiter = RateLimiter() 