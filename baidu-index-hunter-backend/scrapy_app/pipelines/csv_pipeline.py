"""
CSV 导出管道

将爬取的数据导出为 CSV 文件
"""
import os
import csv
import logging
from datetime import datetime
from collections import defaultdict


class CSVExportPipeline:
    """CSV 导出管道"""
    
    def __init__(self, crawler, output_dir, csv_encoding):
        self.crawler = crawler
        self.logger = logging.getLogger(__name__)
        self.output_dir = output_dir
        self.csv_encoding = csv_encoding
        self.files = {}
        self.writers = {}
        self.item_counts = defaultdict(int)
        self.spider_output_dir = None
    
    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        return cls(
            crawler=crawler,
            output_dir=settings.get('OUTPUT_DIR', 'output'),
            csv_encoding=settings.get('OUTPUT_CONFIG', {}).get('csv_encoding', 'utf-8-sig'),
        )
    
    @property
    def spider(self):
        """获取当前 spider 实例"""
        return self.crawler.spider
    
    def open_spider(self):
        """爬虫启动时创建输出目录"""
        spider = self.spider
        task_id = getattr(spider, 'task_id', 'default')
        spider_name = spider.name
        
        # 创建输出目录: output/{spider_name}/{task_id}/
        self.spider_output_dir = os.path.join(self.output_dir, spider_name, task_id)
        os.makedirs(self.spider_output_dir, exist_ok=True)
        
        self.logger.info(f"CSV output directory: {self.spider_output_dir}")
    
    def close_spider(self):
        """爬虫关闭时关闭所有文件"""
        spider = self.spider
        
        for file in self.files.values():
            file.close()
        
        # 输出统计信息
        self.logger.info(f"CSV export completed. Items saved: {dict(self.item_counts)}")
        
        # 更新爬虫的输出文件列表
        if hasattr(spider, 'output_files'):
            spider.output_files = list(self.files.keys())
    
    def process_item(self, item):
        """将 Item 写入 CSV"""
        spider = self.spider
        
        # 跳过 word_check 爬虫
        if spider.name == 'word_check':
            return item
            
        item_type = type(item).__name__
        
        # 跳过内部使用的 Item
        if item_type in ['DecryptKeyItem']:
            return item
        
        # 获取文件路径
        file_path = self._get_file_path(item_type)
        
        if file_path not in self.files:
            self._create_csv_file(file_path, item)
        
        # 写入数据
        writer = self.writers[file_path]
        row_data = self._item_to_dict(item)
        writer.writerow(row_data)
        
        # 刷新文件缓冲区（每100条刷新一次）
        self.item_counts[item_type] += 1
        if self.item_counts[item_type] % 100 == 0:
            self.files[file_path].flush()
        
        return item
    
    def _get_file_path(self, item_type):
        """获取文件路径"""
        spider = self.spider
        task_id = getattr(spider, 'task_id', 'default')
        
        # 根据 Item 类型确定文件名
        file_type_map = {
            'SearchIndexDailyItem': 'daily_data',
            'SearchIndexStatsItem': 'stats_data',
            'FeedIndexDailyItem': 'daily_data',
            'FeedIndexStatsItem': 'stats_data',
            'WordGraphItem': 'word_graph',
            'DemographicItem': 'demographic',
            'InterestItem': 'interest',
            'RegionDistributionItem': 'region_distribution',
        }
        
        file_suffix = file_type_map.get(item_type, 'data')
        filename = f"{spider.name}_{task_id}_{file_suffix}.csv"
        
        return os.path.join(self.spider_output_dir, filename)
    
    def _create_csv_file(self, file_path, item):
        """创建 CSV 文件"""
        # 检查文件是否已存在
        file_exists = os.path.isfile(file_path)
        
        # 打开文件（追加模式）
        file = open(file_path, 'a', newline='', encoding=self.csv_encoding)
        
        # 获取字段名（排除内部字段）
        fieldnames = [key for key in item.keys() if not key.startswith('_')]
        
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction='ignore')
        
        # 如果文件是新创建的，写入表头
        if not file_exists or file.tell() == 0:
            writer.writeheader()
        
        self.files[file_path] = file
        self.writers[file_path] = writer
        
        self.logger.debug(f"Created CSV file: {file_path}")
    
    def _item_to_dict(self, item):
        """将 Item 转换为字典"""
        return {key: value for key, value in item.items() if not key.startswith('_')}
