"""
请求统计中间件

统计请求和响应信息
"""
import logging
import time
from scrapy import signals


class RequestStatsMiddleware:
    """请求统计中间件"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.request_count = 0
        self.response_count = 0
        self.error_count = 0
        self.start_time = None
    
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware
    
    def spider_opened(self, spider):
        """爬虫启动"""
        self.start_time = time.time()
        self.logger.info('Request stats middleware started')
    
    def spider_closed(self, spider, reason):
        """爬虫关闭，输出统计信息"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        self.logger.info(
            f"Spider stats - Requests: {self.request_count}, "
            f"Responses: {self.response_count}, "
            f"Errors: {self.error_count}, "
            f"Duration: {elapsed:.2f}s, "
            f"Avg speed: {self.response_count / elapsed:.2f} req/s" if elapsed > 0 else ""
        )
    
    def process_request(self, request, spider):
        """统计请求"""
        self.request_count += 1
        request.meta['request_start_time'] = time.time()
        return None
    
    def process_response(self, request, response, spider):
        """统计响应"""
        self.response_count += 1
        
        # 计算请求耗时
        start_time = request.meta.get('request_start_time')
        if start_time:
            elapsed = time.time() - start_time
            if elapsed > 5:  # 慢请求警告
                spider.logger.warning(f"Slow request: {request.url} took {elapsed:.2f}s")
        
        return response
    
    def process_exception(self, request, exception, spider):
        """统计异常"""
        self.error_count += 1
        spider.logger.debug(f"Request exception: {exception}")
        return None
