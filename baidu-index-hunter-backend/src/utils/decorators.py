"""
请求重试装饰器模块
"""
import time
import functools
import traceback
import os
from src.core.logger import log
from src.core.config import SPIDER_CONFIG
from src.utils.rate_limiter import rate_limiter

def retry(max_retries=None, delay=None, backoff=None, exceptions=(Exception,)):
    """
    重试装饰器，用于自动重试失败的函数调用
    
    参数:
        max_retries (int): 最大重试次数，默认从SPIDER_CONFIG获取
        delay (float): 初始延迟时间（秒），默认从SPIDER_CONFIG获取
        backoff (float): 重试延迟增长因子，默认为2
        exceptions (tuple): 需要捕获并重试的异常类型
        
    返回:
        function: 装饰后的函数
    """
    max_retries = max_retries if max_retries is not None else SPIDER_CONFIG.get('retry_times', 3)
    delay = delay if delay is not None else SPIDER_CONFIG.get('default_interval', 2)
    backoff = backoff if backoff is not None else 2
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            
            while True:
                try:
                    result = func(*args, **kwargs)
                    
                    # 如果成功，报告成功并返回结果
                    rate_limiter.report_success()
                    return result
                    
                except exceptions as e:
                    retries += 1
                    
                    # 报告失败
                    rate_limiter.report_failure()
                    
                    if retries > max_retries:
                        log.error(f"函数 {func.__name__} 达到最大重试次数 {max_retries}，放弃重试")
                        log.error(f"最后一次异常: {str(e)}")
                        log.debug(traceback.format_exc())
                        raise
                    
                    log.warning(f"函数 {func.__name__} 调用失败 (重试 {retries}/{max_retries}): {str(e)}")
                    log.debug(f"等待 {current_delay} 秒后重试...")
                    
                    # 等待一段时间后重试
                    time.sleep(current_delay)
                    
                    # 增加延迟时间
                    current_delay *= backoff
        
        return wrapper
    
    return decorator
