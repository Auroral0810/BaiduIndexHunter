"""
Spider 中间件

处理爬虫的输入和输出
"""
import logging
from scrapy import signals


class BaiduIndexSpiderMiddleware:
    """百度指数爬虫中间件"""
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls(crawler)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware
    
    @property
    def spider(self):
        """获取当前 spider 实例"""
        return self.crawler.spider
    
    def spider_opened(self, spider):
        self.logger.info(f'Spider middleware opened for: {spider.name}')
    
    def process_spider_input(self, response):
        """处理爬虫输入（响应）"""
        return None
    
    async def process_spider_output(self, response, result):
        """处理爬虫输出（Items 和 Requests）"""
        async for item_or_request in result:
            yield item_or_request
    
    def process_spider_exception(self, response, exception):
        """处理爬虫异常"""
        spider = self.spider
        spider.logger.error(f"Spider exception: {exception}")
        return None
    
    async def process_start(self, start):
        """处理起始请求（Scrapy 2.13+ 新 API）"""
        async for item_or_request in start:
            yield item_or_request
