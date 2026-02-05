"""
百度指数数据处理服务 - 代理模块
该模块现在作为门面（Facade），将实际处理逻辑委托给 specialized engine processors。
"""
from src.core.logger import log
from src.services.storage_service import storage_service

# 导入各个领域的处理器
from src.engine.processors.search_processor import search_processor
from src.engine.processors.demographic_processor import demographic_processor
from src.engine.processors.region_processor import region_processor
from src.engine.processors.word_graph_processor import word_graph_processor
from src.engine.processors.feed_processor import feed_processor

class BaiduIndexDataProcessor:
    """
    百度指数数据处理器门面
    为了保持向后兼容，保留了所有原有方法名，但内部逻辑已委托给 specialized processors。
    """
    
    def __init__(self):
        self._first_data_printed = False

    # --- 代理到 SearchProcessor ---
    def process_search_index_data(self, *args, **kwargs):
        return search_processor.process_search_index_data(*args, **kwargs)

    def process_trend_index_data(self, *args, **kwargs):
        return search_processor.process_trend_index_data(*args, **kwargs)

    def process_search_index_daily_data(self, *args, **kwargs):
        """代理到 SearchProcessor 处理日度数据"""
        return search_processor.process_search_index_daily_data(*args, **kwargs)

    def process_multi_search_index_data(self, *args, **kwargs):
        """代理到 SearchProcessor 处理批量数据"""
        return search_processor.process_multi_search_index_data(*args, **kwargs)

    # --- 代理到 DemographicProcessor ---
    def process_demographic_data(self, *args, **kwargs):
        return demographic_processor.process_demographic_data(*args, **kwargs)

    def process_interest_profile_data(self, *args, **kwargs):
        # 兴趣分布属于 Demographic 范畴
        return demographic_processor.process_interest_profile_data(*args, **kwargs) if hasattr(demographic_processor, 'process_interest_profile_data') else None

    # --- 代理到 WordGraphProcessor ---
    def process_word_graph_data(self, *args, **kwargs):
        return word_graph_processor.process_word_graph_data(*args, **kwargs)

    # --- 代理到 RegionProcessor ---
    def process_region_distribution_data(self, *args, **kwargs):
        return region_processor.process_region_distribution_data(*args, **kwargs)

    # --- 代理到 FeedProcessor ---
    def process_feed_index_data(self, *args, **kwargs):
        return feed_processor.process_feed_index_data(*args, **kwargs)

    # --- 代理到 StorageService (I/O 逻辑) ---
    def save_to_excel(self, df, output_file='百度指数数据.xlsx'):
        return storage_service.save_to_excel(df, output_file)

    def append_to_excel(self, df, output_file='百度指数数据.xlsx'):
        return storage_service.append_to_excel(df, output_file)

    def save_to_csv(self, df, output_file='百度指数数据.csv'):
        return storage_service.save_to_csv(df, output_file)

    def append_to_csv(self, df, output_file='百度指数数据.csv'):
        return storage_service.append_to_csv(df, output_file)

# 创建数据处理器单例
data_processor = BaiduIndexDataProcessor()