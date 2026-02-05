"""
Cookie 轮换中间件

负责为每个请求分配可用的 Cookie，并处理 Cookie 失效的情况
"""
import logging
import json
from scrapy import signals
from scrapy.exceptions import IgnoreRequest


class NoCookieAvailableError(Exception):
    """无可用 Cookie 异常"""
    pass


class CookieRotationMiddleware:
    """Cookie 轮换中间件"""
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.logger = logging.getLogger(__name__)
        self.cookie_rotator = None
        self.cookie_config = crawler.settings.get('COOKIE_CONFIG', {})
    
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls(crawler)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware
    
    @property
    def spider(self):
        """获取当前 spider 实例"""
        return self.crawler.spider
    
    def spider_opened(self, spider):
        """爬虫启动时初始化 Cookie 轮换器"""
        try:
            from cookie_manager.cookie_rotator import CookieRotator
            self.cookie_rotator = CookieRotator()
            self.logger.info('Cookie rotation middleware initialized')
        except Exception as e:
            self.logger.error(f'Failed to initialize cookie rotator: {e}')
            raise
    
    def spider_closed(self, spider):
        """爬虫关闭时清理资源"""
        self.logger.info('Cookie rotation middleware closed')
    
    def process_request(self, request):
        """为请求添加 Cookie"""
        spider = self.spider
        
        # 跳过不需要 Cookie 的请求
        if request.meta.get('skip_cookie', False):
            return None
        
        # 跳过获取解密密钥的请求（使用上一个请求的 Cookie）
        if 'Interface/ptbk' in request.url:
            # 从 meta 中获取之前使用的 Cookie
            if 'cookie_str' in request.meta:
                request.headers['Cookie'] = request.meta['cookie_str']
            return None
        
        try:
            account_id, cookie_dict = self.cookie_rotator.get_cookie()
            
            if not cookie_dict:
                spider.logger.warning("No available cookies")
                # 设置标记，让爬虫知道没有可用 Cookie
                request.meta['no_cookie_available'] = True
                raise NoCookieAvailableError("No available cookies")
            
            # 将 cookie_dict 转换为 Cookie 字符串并设置为请求头
            # 这是关键修复！Scrapy 内置的 CookiesMiddleware 被禁用了，
            # 所以我们必须手动将 cookie 设置为请求头
            cookie_str = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
            request.headers['Cookie'] = cookie_str
            
            # 保存信息到 meta 中，用于重试和日志
            request.meta['cookie_account_id'] = account_id
            request.meta['cookie_dict'] = cookie_dict
            request.meta['cookie_str'] = cookie_str
            
            spider.logger.debug(f"Using cookie from account: {account_id}")
            
        except NoCookieAvailableError:
            raise
        except Exception as e:
            spider.logger.error(f"Failed to get cookie: {e}")
            request.meta['cookie_error'] = str(e)
        
        return None
    
    def process_response(self, request, response):
        """处理响应，检查 Cookie 状态"""
        spider = self.spider
        
        # 跳过获取解密密钥的请求
        if 'Interface/ptbk' in request.url:
            return response
        
        try:
            data = json.loads(response.text)
            status = data.get('status')
            
            account_id = request.meta.get('cookie_account_id')
            
            if status == 10001:
                # Cookie 被临时锁定
                spider.logger.warning(f"Cookie temporarily locked: {account_id}")
                if account_id and self.cookie_rotator:
                    self.cookie_rotator.report_cookie_status(account_id, False)
                # 标记需要重试
                request.meta['cookie_locked'] = True
                return self._retry_with_new_cookie(request, 'Cookie locked', response)
            
            elif status == 10000:
                # Cookie 无效或过期
                spider.logger.warning(f"Cookie invalid or expired: {account_id}")
                if account_id and self.cookie_rotator:
                    self.cookie_rotator.report_cookie_status(account_id, False, permanent=True)
                request.meta['cookie_invalid'] = True
                return self._retry_with_new_cookie(request, 'Cookie invalid', response)
            
        except json.JSONDecodeError:
            pass
        except Exception as e:
            spider.logger.debug(f"Process response error: {e}")
        
        return response
    
    def process_exception(self, request, exception):
        """处理请求异常"""
        spider = self.spider
        
        if isinstance(exception, NoCookieAvailableError):
            spider.logger.error("No cookie available, stopping spider")
            # 触发爬虫暂停
            self.crawler.engine.close_spider(spider, 'no_cookie_available')
            raise IgnoreRequest("No cookie available")
        
        return None
    
    def _retry_with_new_cookie(self, request, reason, response=None):
        """使用新 Cookie 重试请求"""
        spider = self.spider
        retry_times = request.meta.get('cookie_retry_times', 0) + 1
        max_retry = 3
        
        if retry_times <= max_retry:
            spider.logger.info(f"Retrying with new cookie ({retry_times}/{max_retry}): {reason}")
            new_request = request.copy()
            new_request.meta['cookie_retry_times'] = retry_times
            new_request.dont_filter = True
            # 清除之前的 Cookie 信息，让下次请求获取新的
            new_request.meta.pop('cookie_account_id', None)
            new_request.meta.pop('cookie_dict', None)
            new_request.cookies = {}
            return new_request
        
        spider.logger.error(f"Max cookie retries reached for: {request.url}")
        # 返回原始响应而不是 None（Scrapy 要求 process_response 必须返回 Response 或 Request）
        return response
