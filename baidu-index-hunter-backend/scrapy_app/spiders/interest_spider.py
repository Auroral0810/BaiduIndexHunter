"""
兴趣分布爬虫

爬取百度指数兴趣分布数据
"""
import json
import scrapy
from datetime import datetime
from urllib.parse import quote

from .base_spider import BaseBaiduIndexSpider
from scrapy_app.items import InterestItem


class InterestSpider(BaseBaiduIndexSpider):
    """兴趣分布爬虫"""
    
    name = 'interest'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch_size = int(kwargs.get('batch_size', 10))
        self._setup_jobdir()
        
        # 重新计算总任务数
        self.total_items = len(self.keywords)
    
    def _calculate_total_items(self):
        """兴趣分布只与关键词数量相关"""
        self.total_items = len(self.keywords)
    
    def start_requests(self):
        """生成所有请求"""
        base_url = self.settings.get('BAIDU_INDEX_API', {}).get(
            'interest_url', 
            'https://index.baidu.com/api/SocialApi/interest'
        )
        
        for i in range(0, len(self.keywords), self.batch_size):
            batch_keywords = self.keywords[i:i + self.batch_size]
            
            word_list = [[{"name": kw, "wordType": 1}] for kw in batch_keywords]
            word_param = quote(json.dumps(word_list, ensure_ascii=False))
            
            url = f"{base_url}?wordlist={word_param}"
            
            yield self.make_request(
                url=url,
                callback=self.parse,
                meta={
                    'keywords': batch_keywords,
                },
                priority=1,
            )
    
    def parse(self, response):
        """解析兴趣分布响应"""
        try:
            data = json.loads(response.text)
            
            status = data.get('status')
            if status != 0:
                self.logger.warning(f"API error: status={status}")
                self.failed_items += len(response.meta['keywords'])
                return
            
            keywords = response.meta['keywords']
            result_data = data.get('data', {}).get('result', [])
            crawl_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for i, keyword in enumerate(keywords):
                if i >= len(result_data):
                    self.failed_items += 1
                    continue
                
                keyword_data = result_data[i]
                interest_list = keyword_data.get('interest', [])
                
                for interest_item in interest_list:
                    item = InterestItem()
                    item['task_id'] = self.task_id
                    item['keyword'] = keyword
                    item['interest_category'] = interest_item.get('typeId', '')
                    item['interest_name'] = interest_item.get('desc', '')
                    item['ratio'] = interest_item.get('rate', 0)
                    item['tgi'] = interest_item.get('tgi', 0)
                    item['crawl_time'] = crawl_time
                    
                    yield item
                
                self.completed_items += 1
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            self.failed_items += len(response.meta.get('keywords', []))
        except Exception as e:
            self.logger.error(f"Parse error: {e}")
            self.failed_items += len(response.meta.get('keywords', []))
