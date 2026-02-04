"""
数据验证管道

验证数据的完整性和有效性
"""
import logging
from scrapy.exceptions import DropItem


class DataValidationPipeline:
    """数据验证管道"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 定义必需字段
        self.required_fields = {
            'SearchIndexDailyItem': ['keyword', 'city_code', 'date', 'all_index'],
            'SearchIndexStatsItem': ['keyword', 'city_code', 'date_range'],
            'FeedIndexDailyItem': ['keyword', 'city_code', 'date', 'feed_index'],
            'FeedIndexStatsItem': ['keyword', 'city_code', 'date_range'],
            'WordGraphItem': ['keyword', 'date', 'related_word'],
            'DemographicItem': ['keyword'],
            'InterestItem': ['keyword', 'interest_category'],
            'RegionDistributionItem': ['keyword', 'date', 'province_code'],
        }
    
    def process_item(self, item, spider):
        """验证 Item"""
        item_type = type(item).__name__
        
        # 获取必需字段
        required = self.required_fields.get(item_type, [])
        
        # 验证必需字段
        missing_fields = []
        for field in required:
            if field not in item or item.get(field) is None:
                missing_fields.append(field)
        
        if missing_fields:
            raise DropItem(f"Missing required fields: {missing_fields}")
        
        # 数据清洗
        item = self._clean_data(item)
        
        return item
    
    def _clean_data(self, item):
        """清洗数据"""
        # 处理字符串字段的空白
        for key, value in item.items():
            if isinstance(value, str):
                item[key] = value.strip()
        
        # 处理数值字段
        numeric_fields = ['all_index', 'wise_index', 'pc_index', 'feed_index', 
                          'ratio', 'pv', 'tgi', 'rank']
        for field in numeric_fields:
            if field in item:
                value = item[field]
                if value == '' or value == '-' or value is None:
                    item[field] = '0'
                elif isinstance(value, str):
                    # 移除千分位分隔符
                    item[field] = value.replace(',', '')
        
        return item
