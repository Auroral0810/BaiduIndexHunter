"""
资讯指数爬虫

爬取百度资讯指数的日度数据
"""
import json
import scrapy
from datetime import datetime

from .base_spider import BaseBaiduIndexSpider
from scrapy_app.items import FeedIndexDailyItem, FeedIndexStatsItem


class FeedIndexSpider(BaseBaiduIndexSpider):
    """资讯指数爬虫"""
    
    name = 'feed_index'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch_size = int(kwargs.get('batch_size', 5))
        self._setup_jobdir()
    
    def start_requests(self):
        """生成所有请求"""
        base_url = self.settings.get('BAIDU_INDEX_API', {}).get(
            'feed_url', 
            'https://index.baidu.com/api/FeedSearchApi/getFeedIndex'
        )
        
        # 按批次处理关键词
        for i in range(0, len(self.keywords), self.batch_size):
            batch_keywords = self.keywords[i:i + self.batch_size]
            
            for city_code, city_name in self.cities.items():
                for start_date, end_date in self.date_ranges:
                    # 构建 word 参数
                    word_param = self.build_word_param(batch_keywords)
                    
                    url = (
                        f"{base_url}?"
                        f"area={city_code}&"
                        f"word={word_param}&"
                        f"startDate={start_date}&"
                        f"endDate={end_date}"
                    )
                    
                    yield self.make_request(
                        url=url,
                        callback=self.parse,
                        meta={
                            'keywords': batch_keywords,
                            'city_code': city_code,
                            'city_name': city_name,
                            'start_date': start_date,
                            'end_date': end_date,
                        },
                        priority=1,
                    )
    
    def parse(self, response):
        """解析资讯指数响应"""
        try:
            data = json.loads(response.text)
            
            status = data.get('status')
            if status != 0:
                self.logger.warning(f"API error: status={status}")
                self.failed_items += len(response.meta['keywords'])
                return
            
            if not data.get('data') or not data['data'].get('index'):
                self.logger.warning("Empty data in response")
                self.failed_items += len(response.meta['keywords'])
                return
            
            # 获取解密密钥
            uniqid = data['data']['uniqid']
            ptbk_url = self.build_ptbk_url(uniqid)
            
            yield self.make_request(
                url=ptbk_url,
                callback=self.parse_with_key,
                meta={
                    'original_data': data,
                    'keywords': response.meta['keywords'],
                    'city_code': response.meta['city_code'],
                    'city_name': response.meta['city_name'],
                    'start_date': response.meta['start_date'],
                    'end_date': response.meta['end_date'],
                    'cookie_dict': response.meta.get('cookie_dict'),
                    'skip_cipher': True,
                },
            )
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            self.failed_items += len(response.meta.get('keywords', []))
        except Exception as e:
            self.logger.error(f"Parse error: {e}")
            self.failed_items += len(response.meta.get('keywords', []))
    
    def parse_with_key(self, response):
        """使用解密密钥解析数据"""
        try:
            key_data = json.loads(response.text)
            
            if key_data.get('status') != 0:
                self.logger.error(f"Failed to get decrypt key")
                return
            
            key = key_data.get('data')
            if not key:
                self.logger.error("Empty decrypt key")
                return
            
            meta = response.meta
            original_data = meta['original_data']
            keywords = meta['keywords']
            city_code = meta['city_code']
            city_name = meta['city_name']
            start_date = meta['start_date']
            end_date = meta['end_date']
            
            index_data = original_data['data']['index']
            
            dates = self.generate_dates(start_date, end_date)
            crawl_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for i, keyword in enumerate(keywords):
                if i >= len(index_data):
                    self.failed_items += 1
                    continue
                
                feed_data_encrypted = index_data[i].get('data', '')
                feed_data = self.decrypt_data(key, feed_data_encrypted)
                feed_values = feed_data.split(',') if feed_data else []
                
                # 生成日度数据项
                for j, date in enumerate(dates):
                    item = FeedIndexDailyItem()
                    item['task_id'] = self.task_id
                    item['keyword'] = keyword
                    item['city_code'] = city_code
                    item['city_name'] = city_name
                    item['date'] = date
                    item['data_type'] = '日度'
                    item['data_interval'] = 1
                    item['year'] = date[:4]
                    item['feed_index'] = feed_values[j] if j < len(feed_values) else '0'
                    item['crawl_time'] = crawl_time
                    
                    yield item
                
                # 生成统计数据项
                stats_item = self._build_stats_item(
                    keyword, city_code, city_name, start_date, end_date,
                    feed_values, crawl_time
                )
                yield stats_item
                
                self.completed_items += 1
                
        except Exception as e:
            self.logger.error(f"Parse with key error: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _build_stats_item(self, keyword, city_code, city_name, start_date, end_date,
                          feed_values, crawl_time):
        """构建统计数据项"""
        item = FeedIndexStatsItem()
        item['task_id'] = self.task_id
        item['keyword'] = keyword
        item['city_code'] = city_code
        item['city_name'] = city_name
        item['date_range'] = f"{start_date} 至 {end_date}"
        item['crawl_time'] = crawl_time
        
        feed_nums = [int(v) for v in feed_values if v and v != '0' and v != '']
        
        item['feed_avg'] = round(sum(feed_nums) / len(feed_nums), 2) if feed_nums else 0
        item['feed_sum'] = sum(feed_nums)
        item['feed_yoy'] = '-'
        item['feed_qoq'] = '-'
        
        return item
