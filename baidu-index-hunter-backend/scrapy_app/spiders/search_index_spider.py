"""
搜索指数爬虫

爬取百度搜索指数的日度、周度数据
"""
import json
import scrapy
from datetime import datetime

from .base_spider import BaseBaiduIndexSpider
from scrapy_app.items import SearchIndexDailyItem, SearchIndexStatsItem


class SearchIndexSpider(BaseBaiduIndexSpider):
    """搜索指数爬虫"""
    
    name = 'search_index'
    
    # 自定义设置
    custom_settings = {
        'KEYWORDS_BATCH_SIZE': 5,  # 每批处理的关键词数量
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch_size = int(kwargs.get('batch_size', 5))
        self._setup_jobdir()
    
    async def start(self):
        """生成所有请求（Scrapy 2.13+ 新 API）"""
        base_url = self.settings.get('BAIDU_INDEX_API', {}).get(
            'search_url', 
            'https://index.baidu.com/api/SearchApi/index'
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
        """解析搜索指数响应"""
        try:
            data = json.loads(response.text)
            
            # 检查响应状态
            status = data.get('status')
            if status != 0:
                self.logger.warning(f"API error: status={status}, message={data.get('message', '')}")
                self.failed_items += len(response.meta['keywords'])
                return
            
            # 检查数据完整性
            if not data.get('data') or not data['data'].get('userIndexes'):
                self.logger.warning("Empty data in response")
                self.failed_items += len(response.meta['keywords'])
                return
            
            # 获取解密密钥
            uniqid = data['data']['uniqid']
            ptbk_url = self.build_ptbk_url(uniqid)
            
            # 请求解密密钥
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
                    'cookie_dict': response.meta.get('cookie_dict'),  # 传递 Cookie
                    'skip_cipher': True,  # 不需要 Cipher-Text
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
                self.logger.error(f"Failed to get decrypt key: {key_data}")
                return
            
            key = key_data.get('data')
            if not key:
                self.logger.error("Empty decrypt key")
                return
            
            # 获取元数据
            meta = response.meta
            original_data = meta['original_data']
            keywords = meta['keywords']
            city_code = meta['city_code']
            city_name = meta['city_name']
            start_date = meta['start_date']
            end_date = meta['end_date']
            
            user_indexes = original_data['data']['userIndexes']
            general_ratio = original_data['data'].get('generalRatio', [])
            
            # 生成日期列表
            dates = self.generate_dates(start_date, end_date)
            crawl_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 处理每个关键词的数据
            for i, keyword in enumerate(keywords):
                if i >= len(user_indexes):
                    self.logger.warning(f"No data for keyword: {keyword}")
                    self.failed_items += 1
                    continue
                
                user_index = user_indexes[i]
                
                # 解密各终端数据
                all_data = self.decrypt_data(key, user_index.get('all', {}).get('data', ''))
                wise_data = self.decrypt_data(key, user_index.get('wise', {}).get('data', ''))
                pc_data = self.decrypt_data(key, user_index.get('pc', {}).get('data', ''))
                
                # 分割数据
                all_values = all_data.split(',') if all_data else []
                wise_values = wise_data.split(',') if wise_data else []
                pc_values = pc_data.split(',') if pc_data else []
                
                # 生成日度数据项
                for j, date in enumerate(dates):
                    item = SearchIndexDailyItem()
                    item['task_id'] = self.task_id
                    item['keyword'] = keyword
                    item['city_code'] = city_code
                    item['city_name'] = city_name
                    item['date'] = date
                    item['data_type'] = '日度'
                    item['data_interval'] = 1
                    item['year'] = date[:4]
                    item['all_index'] = all_values[j] if j < len(all_values) else '0'
                    item['wise_index'] = wise_values[j] if j < len(wise_values) else '0'
                    item['pc_index'] = pc_values[j] if j < len(pc_values) else '0'
                    item['crawl_time'] = crawl_time
                    
                    yield item
                
                # 生成统计数据项
                stats_item = self._build_stats_item(
                    keyword, city_code, city_name, start_date, end_date,
                    all_values, wise_values, pc_values,
                    general_ratio[i] if i < len(general_ratio) else {},
                    crawl_time
                )
                yield stats_item
                
                self.completed_items += 1
            
        except Exception as e:
            self.logger.error(f"Parse with key error: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _build_stats_item(self, keyword, city_code, city_name, start_date, end_date,
                          all_values, wise_values, pc_values, ratio_data, crawl_time):
        """构建统计数据项"""
        item = SearchIndexStatsItem()
        item['task_id'] = self.task_id
        item['keyword'] = keyword
        item['city_code'] = city_code
        item['city_name'] = city_name
        item['date_range'] = f"{start_date} 至 {end_date}"
        item['crawl_time'] = crawl_time
        
        # 计算整体数据
        all_nums = [int(v) for v in all_values if v and v != '0' and v != '']
        wise_nums = [int(v) for v in wise_values if v and v != '0' and v != '']
        pc_nums = [int(v) for v in pc_values if v and v != '0' and v != '']
        
        # 整体
        item['all_avg'] = round(sum(all_nums) / len(all_nums), 2) if all_nums else 0
        item['all_sum'] = sum(all_nums)
        item['all_yoy'] = ratio_data.get('all', {}).get('yoy', '-') if isinstance(ratio_data.get('all'), dict) else '-'
        item['all_qoq'] = ratio_data.get('all', {}).get('qoq', '-') if isinstance(ratio_data.get('all'), dict) else '-'
        
        # 移动
        item['wise_avg'] = round(sum(wise_nums) / len(wise_nums), 2) if wise_nums else 0
        item['wise_sum'] = sum(wise_nums)
        item['wise_yoy'] = ratio_data.get('wise', {}).get('yoy', '-') if isinstance(ratio_data.get('wise'), dict) else '-'
        item['wise_qoq'] = ratio_data.get('wise', {}).get('qoq', '-') if isinstance(ratio_data.get('wise'), dict) else '-'
        
        # PC
        item['pc_avg'] = round(sum(pc_nums) / len(pc_nums), 2) if pc_nums else 0
        item['pc_sum'] = sum(pc_nums)
        item['pc_yoy'] = ratio_data.get('pc', {}).get('yoy', '-') if isinstance(ratio_data.get('pc'), dict) else '-'
        item['pc_qoq'] = ratio_data.get('pc', {}).get('qoq', '-') if isinstance(ratio_data.get('pc'), dict) else '-'
        
        return item
