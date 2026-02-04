"""
地域分布爬虫

爬取百度指数地域分布数据
"""
import json
import scrapy
from datetime import datetime

from .base_spider import BaseBaiduIndexSpider
from scrapy_app.items import RegionDistributionItem


class RegionSpider(BaseBaiduIndexSpider):
    """地域分布爬虫"""
    
    name = 'region'
    
    def __init__(self, regions=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.regions = self._parse_regions(regions)
        self._setup_jobdir()
        
        # 重新计算总任务数
        self.total_items = len(self.keywords) * len(self.regions) * len(self.date_ranges)
    
    def _parse_regions(self, regions):
        """解析地区参数"""
        if regions is None:
            return [0]  # 默认全国
        
        if isinstance(regions, str):
            try:
                regions = json.loads(regions)
            except json.JSONDecodeError:
                regions = [r.strip() for r in regions.split(',') if r.strip()]
        
        if isinstance(regions, list):
            return [int(r) for r in regions]
        
        return [int(regions)]
    
    def _calculate_total_items(self):
        """地域分布的总任务数"""
        region_count = len(self.regions) if hasattr(self, 'regions') else 1
        self.total_items = len(self.keywords) * region_count * len(self.date_ranges)
    
    def start_requests(self):
        """生成所有请求"""
        base_url = self.settings.get('BAIDU_INDEX_API', {}).get(
            'region_url', 
            'https://index.baidu.com/api/SearchApi/region'
        )
        
        for keyword in self.keywords:
            for region in self.regions:
                for start_date, end_date in self.date_ranges:
                    # 构建 word 参数
                    word_param = self.build_word_param([keyword])
                    
                    url = (
                        f"{base_url}?"
                        f"region={region}&"
                        f"word={word_param}&"
                        f"startDate={start_date}&"
                        f"endDate={end_date}"
                    )
                    
                    yield self.make_request(
                        url=url,
                        callback=self.parse,
                        meta={
                            'keyword': keyword,
                            'region': region,
                            'start_date': start_date,
                            'end_date': end_date,
                        },
                        priority=1,
                    )
    
    def parse(self, response):
        """解析地域分布响应"""
        try:
            data = json.loads(response.text)
            
            status = data.get('status')
            if status != 0:
                self.logger.warning(f"API error: status={status}")
                self.failed_items += 1
                return
            
            keyword = response.meta['keyword']
            start_date = response.meta['start_date']
            end_date = response.meta['end_date']
            crawl_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            region_data = data.get('data', {}).get('region', [])
            
            if not region_data:
                self.logger.warning(f"No region data for: {keyword}")
                self.failed_items += 1
                return
            
            # 处理第一个关键词的数据
            word_region_data = region_data[0] if region_data else {}
            
            # 处理省份数据
            province_data = word_region_data.get('prov', [])
            rank = 1
            
            for prov in province_data:
                item = RegionDistributionItem()
                item['task_id'] = self.task_id
                item['keyword'] = keyword
                item['date'] = f"{start_date} 至 {end_date}"
                item['province_code'] = prov.get('code', '')
                item['province_name'] = prov.get('name', '')
                item['city_code'] = ''
                item['city_name'] = ''
                item['ratio'] = prov.get('rate', 0)
                item['rank'] = rank
                item['crawl_time'] = crawl_time
                
                rank += 1
                yield item
            
            # 处理城市数据
            city_data = word_region_data.get('city', [])
            city_rank = 1
            
            for city in city_data:
                item = RegionDistributionItem()
                item['task_id'] = self.task_id
                item['keyword'] = keyword
                item['date'] = f"{start_date} 至 {end_date}"
                item['province_code'] = city.get('pcode', '')
                item['province_name'] = city.get('pname', '')
                item['city_code'] = city.get('code', '')
                item['city_name'] = city.get('name', '')
                item['ratio'] = city.get('rate', 0)
                item['rank'] = city_rank
                item['crawl_time'] = crawl_time
                
                city_rank += 1
                yield item
            
            self.completed_items += 1
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            self.failed_items += 1
        except Exception as e:
            self.logger.error(f"Parse error: {e}")
            self.failed_items += 1
