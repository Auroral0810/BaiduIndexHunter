"""
Spider 中间件

处理爬虫的输入和输出
"""
import logging
from scrapy import signals


class BaiduIndexSpiderMiddleware:
    """百度指数爬虫中间件"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware
    
    def spider_opened(self, spider):
        self.logger.info(f'Spider middleware opened for: {spider.name}')
    
    def process_spider_input(self, response, spider):
        """处理爬虫输入（响应）"""
        return None
    
    def process_spider_output(self, response, result, spider):
        """处理爬虫输出（Items 和 Requests）"""
        for item_or_request in result:
            yield item_or_request
    
    def process_spider_exception(self, response, exception, spider):
        """处理爬虫异常"""
        spider.logger.error(f"Spider exception: {exception}")
        return None
    
    def process_start_requests(self, start_requests, spider):
        """处理起始请求"""
        for request in start_requests:
            yield request
