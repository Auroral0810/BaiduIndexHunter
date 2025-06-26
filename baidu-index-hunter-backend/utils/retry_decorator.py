"""
请求重试装饰器模块
"""
import time
import functools
from utils.logger import log
from config.settings import SPIDER_CONFIG
from cookie_manager.cookie_rotator import cookie_rotator


def retry(max_retries=None, delay=0.3):
    """
    请求重试装饰器
    :param max_retries: 最大重试次数，默认使用配置值
    :param delay: 重试间隔，单位秒
    """
    max_retries = max_retries if max_retries is not None else SPIDER_CONFIG['retry_times']
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            last_error = None
            
            # 定义检查是否与Cookie相关的辅助函数
            def is_cookie_related_error(message):
                cookie_error_keywords = [
                    "无可用Cookie", 
                    "无法获取Cookie", 
                    "所有Cookie都已被锁定", 
                    "没有可用的Cookie",
                    "Cookie全部被锁定"
                ]
                return any(keyword in message for keyword in cookie_error_keywords)
            
            while retries <= max_retries:
                try:
                    # 检查cookie是否可用，如果不可用则等待
                    if not cookie_rotator.cookies_available_event.is_set():
                        log.info(f"{func.__name__} 等待Cookie可用...")
                        # 等待cookie可用，最多等待10分钟
                        if not cookie_rotator.wait_for_available_cookie(timeout=600):
                            log.warning(f"{func.__name__} 等待Cookie超时，跳过等待继续尝试")
                        else:
                            log.info(f"Cookie已可用，继续执行 {func.__name__}")
                    
                    if retries > 0:
                        log.warning(f"第 {retries} 次重试 {func.__name__}")
                    
                    result = func(*args, **kwargs)
                    
                    # 如果请求成功且返回结果不为None，直接返回结果
                    if result is not None:
                        return result
                    
                    # 检查是否是由于没有可用Cookie导致的失败
                    last_log = log.last_message()
                    if is_cookie_related_error(last_log):
                        log.warning(f"{func.__name__} 因无可用Cookie而失败，等待Cookie可用后重试")
                        
                        # 等待cookie可用，最多等待10分钟
                        if not cookie_rotator.wait_for_available_cookie(timeout=600):
                            log.warning(f"{func.__name__} 等待Cookie超时，不再重试")
                            # 等待一段时间再返回，避免频繁请求
                            time.sleep(5)
                            return None
                        
                        log.info(f"Cookie已可用，重试 {func.__name__}")
                        continue
                    
                    # 如果返回结果为None，认为请求失败，需要重试
                    log.warning(f"{func.__name__} 返回空结果，准备重试")
                    
                except Exception as e:
                    log.error(f"{func.__name__} 执行失败: {e}")
                    last_error = str(e)
                    # 检查异常信息是否与Cookie相关
                    if is_cookie_related_error(last_error):
                        log.warning(f"{func.__name__} 因无可用Cookie而失败，等待Cookie可用后重试")
                        
                        # 等待cookie可用，最多等待10分钟
                        if not cookie_rotator.wait_for_available_cookie(timeout=600):
                            log.warning(f"{func.__name__} 等待Cookie超时，不再重试")
                            # 等待一段时间再返回，避免频繁请求
                            time.sleep(5)
                            return None
                        
                        log.info(f"Cookie已可用，重试 {func.__name__}")
                        continue
                
                # 如果达到最大重试次数，放弃重试
                if retries == max_retries:
                    log.error(f"{func.__name__} 已达到最大重试次数 {max_retries}，放弃重试")
                    return None
                
                # 重试前等待一段时间
                time.sleep(delay * (2 ** retries))  # 指数退避策略
                retries += 1
            
            return None
        
        return wrapper
    
    return decorator 