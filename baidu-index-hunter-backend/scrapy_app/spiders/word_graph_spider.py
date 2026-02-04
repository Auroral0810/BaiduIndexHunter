"""
需求图谱爬虫

爬取百度需求图谱数据（相关词、来源/去向检索词）
"""
import json
import scrapy
from datetime import datetime
from urllib.parse import quote

from .base_spider import BaseBaiduIndexSpider
from scrapy_app.items import WordGraphItem


class WordGraphSpider(BaseBaiduIndexSpider):
    """需求图谱爬虫"""
    
    name = 'word_graph'
    
    def __init__(self, datelists=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 需求图谱使用特殊的日期列表格式
        self.datelists = self._parse_datelists(datelists)
        self._setup_jobdir()
        
        # 重新计算总任务数
        self.total_items = len(self.keywords) * len(self.datelists)
    
    def _parse_datelists(self, datelists):
        """解析日期列表参数"""
        if datelists is None:
            # 默认使用最近的日期
            return [datetime.now().strftime('%Y-%m-%d')]
        
        if isinstance(datelists, str):
            try:
                datelists = json.loads(datelists)
            except json.JSONDecodeError:
                return [d.strip() for d in datelists.split(',') if d.strip()]
        
        if isinstance(datelists, list):
            return datelists
        
        return [str(datelists)]
    
    def start_requests(self):
        """生成所有请求"""
        base_url = self.settings.get('BAIDU_INDEX_API', {}).get(
            'word_graph_url', 
            'https://index.baidu.com/api/WordGraph/multi'
        )
        
        for keyword in self.keywords:
            for date in self.datelists:
                # 构建 word 参数
                word_param = quote(json.dumps([{"name": keyword, "wordType": 1}], ensure_ascii=False))
                
                url = f"{base_url}?wordlist={word_param}&datelist={date}"
                
                yield self.make_request(
                    url=url,
                    callback=self.parse,
                    meta={
                        'keyword': keyword,
                        'date': date,
                    },
                    priority=1,
                )
    
    def parse(self, response):
        """解析需求图谱响应"""
        try:
            data = json.loads(response.text)
            
            status = data.get('status')
            if status != 0:
                self.logger.warning(f"API error: status={status}")
                self.failed_items += 1
                return
            
            keyword = response.meta['keyword']
            date = response.meta['date']
            crawl_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            word_data = data.get('data', {}).get('wordlist', [])
            
            if not word_data:
                self.logger.warning(f"No word graph data for: {keyword}")
                self.failed_items += 1
                return
            
            # 处理第一个关键词的数据
            word_info = word_data[0] if word_data else {}
            word_graph = word_info.get('wordGraph', [])
            
            for graph_item in word_graph:
                period = graph_item.get('period', '')
                
                # 处理来源检索词
                source_words = graph_item.get('source', [])
                for source in source_words:
                    item = WordGraphItem()
                    item['task_id'] = self.task_id
                    item['keyword'] = keyword
                    item['date'] = date
                    item['related_word'] = source.get('word', '')
                    item['word_type'] = '来源检索词'
                    item['period'] = period
                    item['pv'] = source.get('pv', 0)
                    item['ratio'] = source.get('ratio', 0)
                    item['crawl_time'] = crawl_time
                    
                    yield item
                
                # 处理去向检索词
                result_words = graph_item.get('result', [])
                for result in result_words:
                    item = WordGraphItem()
                    item['task_id'] = self.task_id
                    item['keyword'] = keyword
                    item['date'] = date
                    item['related_word'] = result.get('word', '')
                    item['word_type'] = '去向检索词'
                    item['period'] = period
                    item['pv'] = result.get('pv', 0)
                    item['ratio'] = result.get('ratio', 0)
                    item['crawl_time'] = crawl_time
                    
                    yield item
            
            self.completed_items += 1
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            self.failed_items += 1
        except Exception as e:
            self.logger.error(f"Parse error: {e}")
            self.failed_items += 1
