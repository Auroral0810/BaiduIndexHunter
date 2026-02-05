"""
智能重试中间件

基于响应状态智能决定是否重试请求
"""
import logging
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message


class SmartRetryMiddleware(RetryMiddleware):
    """智能重试中间件"""
    
    def __init__(self, crawler):
        super().__init__(crawler.settings)
        self.crawler = crawler
        self.logger = logging.getLogger(__name__)
        # 额外的重试状态码
        self.retry_http_codes = set(int(x) for x in crawler.settings.getlist('RETRY_HTTP_CODES'))
        # 百度指数特定的错误状态
        self.baidu_retry_status = {10001, 10002, 10003}  # 临时错误
        self.baidu_permanent_errors = {10000}  # 永久错误（如未登录）
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)
    
    @property
    def spider(self):
        """获取当前 spider 实例"""
        return self.crawler.spider
    
    def process_response(self, request, response):
        """处理响应，决定是否重试"""
        spider = self.spider
        
        # HTTP 状态码重试
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        
        # 检查百度指数 API 响应
        if 'index.baidu.com/api' in request.url or 'Interface/ptbk' in request.url:
            try:
                import json
                data = json.loads(response.text)
                status = data.get('status')
                
                if status in self.baidu_retry_status:
                    # 临时错误，可以重试
                    reason = f"Baidu API error: status={status}"
                    spider.logger.warning(f"Baidu API temporary error: {status}, will retry")
                    return self._retry(request, reason, spider) or response
                
                elif status in self.baidu_permanent_errors:
                    # 永久错误，不重试但记录
                    spider.logger.error(f"Baidu API permanent error: {status}")
                    # 由 Cookie 中间件处理
                    pass
                
            except Exception as e:
                spider.logger.debug(f"Failed to parse response: {e}")
        
        return response
    
    def process_exception(self, request, exception):
        """处理请求异常"""
        spider = self.spider
        
        # 网络错误等异常的重试
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY) \
                and not request.meta.get('dont_retry', False):
            return self._retry(request, exception, spider)
        
        return None
    
    def _retry(self, request, reason, spider):
        """执行重试"""
        retries = request.meta.get('retry_times', 0) + 1
        max_retries = self.max_retry_times
        
        if retries <= max_retries:
            spider.logger.info(f"Retrying {request.url} (attempt {retries}/{max_retries}): {reason}")
            
            retry_request = request.copy()
            retry_request.meta['retry_times'] = retries
            retry_request.dont_filter = True
            
            # 增加延迟
            retry_request.meta['download_delay'] = retries * 0.5
            
            return retry_request
        else:
            spider.logger.error(f"Gave up retrying {request.url}: max retries reached")
            # 记录失败
            spider.failed_items = getattr(spider, 'failed_items', 0) + 1
            return None
