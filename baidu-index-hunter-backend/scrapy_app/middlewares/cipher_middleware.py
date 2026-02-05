"""
Cipher-Text 生成中间件

为百度指数 API 请求生成必要的 Cipher-Text 请求头
"""
import logging
from scrapy import signals
from urllib.parse import unquote


class CipherTextMiddleware:
    """Cipher-Text 生成中间件"""
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.logger = logging.getLogger(__name__)
        self.cipher_generator = None
        self.baidu_api = crawler.settings.get('BAIDU_INDEX_API', {})
    
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
        """爬虫启动时初始化"""
        try:
            from utils.cipher_text import cipher_text_generator
            self.cipher_generator = cipher_text_generator
            self.logger.info('Cipher-Text middleware initialized')
        except Exception as e:
            self.logger.error(f'Failed to initialize cipher generator: {e}')
            raise
    
    def process_request(self, request):
        """为请求添加 Cipher-Text 头"""
        spider = self.spider
        
        # 跳过不需要 Cipher-Text 的请求
        if request.meta.get('skip_cipher', False):
            return None
        
        # 跳过获取解密密钥的请求
        if 'Interface/ptbk' in request.url:
            return None
        
        # 只为百度指数 API 请求添加 Cipher-Text
        if 'index.baidu.com/api' not in request.url:
            return None
        
        try:
            # 从 URL 或 meta 中获取关键词
            keyword = self._extract_keyword(request)
            
            if keyword:
                # 构造 Cipher-Text URL
                encoded_keyword = keyword.replace(' ', '%20')
                referer = self.baidu_api.get('referer', 'https://index.baidu.com/v2/main/index.html')
                cipher_url = f"{referer}#/trend/{encoded_keyword}?words={encoded_keyword}"
                
                # 生成 Cipher-Text
                cipher_text = self.cipher_generator.generate(cipher_url)
                
                if cipher_text:
                    # 设置请求头
                    request.headers['Cipher-Text'] = cipher_text
                    request.headers['Referer'] = referer
                    spider.logger.debug(f"Added Cipher-Text for keyword: {keyword}")
                else:
                    spider.logger.warning(f"Failed to generate Cipher-Text for: {keyword}")
            
        except Exception as e:
            spider.logger.error(f"Cipher-Text middleware error: {e}")
        
        return None
    
    def _extract_keyword(self, request):
        """从请求中提取关键词"""
        # 优先从 meta 中获取
        if 'keywords' in request.meta:
            keywords = request.meta['keywords']
            if isinstance(keywords, list) and len(keywords) > 0:
                return keywords[0]
            return keywords
        
        # 从 URL 中解析
        try:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(request.url)
            params = parse_qs(parsed.query)
            
            if 'word' in params:
                import json
                word_param = unquote(params['word'][0])
                word_list = json.loads(word_param)
                if word_list and len(word_list) > 0:
                    if isinstance(word_list[0], list) and len(word_list[0]) > 0:
                        return word_list[0][0].get('name', '')
                    elif isinstance(word_list[0], dict):
                        return word_list[0].get('name', '')
        except Exception as e:
            self.logger.debug(f"Failed to extract keyword from URL: {e}")
        
        return None
