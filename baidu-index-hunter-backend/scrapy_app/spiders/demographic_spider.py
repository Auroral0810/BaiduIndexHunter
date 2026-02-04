"""
人群属性爬虫

爬取百度指数人群属性数据（年龄分布、性别分布）
"""
import json
import scrapy
from datetime import datetime
from urllib.parse import quote

from .base_spider import BaseBaiduIndexSpider
from scrapy_app.items import DemographicItem


class DemographicSpider(BaseBaiduIndexSpider):
    """人群属性爬虫"""
    
    name = 'demographic'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch_size = int(kwargs.get('batch_size', 10))
        self._setup_jobdir()
        
        # 重新计算总任务数（只跟关键词数量相关）
        self.total_items = len(self.keywords)
    
    def _calculate_total_items(self):
        """人群属性只与关键词数量相关"""
        self.total_items = len(self.keywords)
    
    def start_requests(self):
        """生成所有请求"""
        base_url = self.settings.get('BAIDU_INDEX_API', {}).get(
            'social_url', 
            'https://index.baidu.com/api/SocialApi/baseAttributes'
        )
        
        # 按批次处理关键词
        for i in range(0, len(self.keywords), self.batch_size):
            batch_keywords = self.keywords[i:i + self.batch_size]
            
            # 构建 word 参数
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
        """解析人群属性响应"""
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
                
                # 获取年龄分布
                age_data = keyword_data.get('age', [])
                age_distribution = {}
                age_tgi = {}
                
                for age_item in age_data:
                    age_range = age_item.get('desc', '')
                    age_distribution[age_range] = age_item.get('rate', 0)
                    age_tgi[age_range] = age_item.get('tgi', 0)
                
                # 获取性别分布
                gender_data = keyword_data.get('gender', [])
                gender_distribution = {}
                gender_tgi = {}
                
                for gender_item in gender_data:
                    gender = gender_item.get('desc', '')
                    gender_distribution[gender] = gender_item.get('rate', 0)
                    gender_tgi[gender] = gender_item.get('tgi', 0)
                
                # 创建 Item
                item = DemographicItem()
                item['task_id'] = self.task_id
                item['keyword'] = keyword
                item['age_distribution'] = json.dumps(age_distribution, ensure_ascii=False)
                item['gender_distribution'] = json.dumps(gender_distribution, ensure_ascii=False)
                item['age_tgi'] = json.dumps(age_tgi, ensure_ascii=False)
                item['gender_tgi'] = json.dumps(gender_tgi, ensure_ascii=False)
                item['crawl_time'] = crawl_time
                
                yield item
                
                self.completed_items += 1
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            self.failed_items += len(response.meta.get('keywords', []))
        except Exception as e:
            self.logger.error(f"Parse error: {e}")
            self.failed_items += len(response.meta.get('keywords', []))
