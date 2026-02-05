"""
搜索指数与趋势指数处理器
"""
import pandas as pd
from datetime import datetime
from src.core.logger import log
from src.services.region_service import get_region_manager

region_manager = get_region_manager()

class SearchProcessor:
    """搜索指数数据处理器"""
    
    def _get_days_in_year(self, year):
        """计算指定年份的天数"""
        try:
            year = int(year)
            return 366 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 365
        except:
            return 365

    def process_search_index_data(self, data, city_number, word, year=None):
        """处理搜索指数数据"""
        try:
            if not data or 'data' not in data:
                return pd.DataFrame()
            
            general_ratio = data['data'].get('generalRatio', [{}])[0]
            if not general_ratio:
                return pd.DataFrame()
            
            city_name = region_manager.get_city_name_by_code(city_number) or f"未知城市({city_number})"
            year = year or datetime.now().year
            
            all_avg = general_ratio.get('all', {}).get('avg', 0)
            wise_avg = general_ratio.get('wise', {}).get('avg', 0)
            pc_avg = general_ratio.get('pc', {}).get('avg', 0)
            
            days_in_year = self._get_days_in_year(year)
            
            return pd.DataFrame({
                '搜索关键词': [word],
                '城市': [city_name],
                '城市编号': [city_number],
                '年份': [year],
                '整体日均值': [all_avg],
                '移动日均值': [wise_avg],
                'PC日均值': [pc_avg],
                '整体年总值': [all_avg * days_in_year],
                '移动年总值': [wise_avg * days_in_year],
                'PC年总值': [pc_avg * days_in_year],
                '爬取时间': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            })
        except Exception as e:
            log.error(f"SearchProcessor error: {e}")
            return pd.DataFrame()

    def process_trend_index_data(self, data, area, keyword, year=None):
        """处理趋势指数数据"""
        try:
            if not data or 'data' not in data:
                return pd.DataFrame()
            
            trend_data = data['data'].get('index', [{}])[0]
            if not trend_data:
                return pd.DataFrame()
            
            city_name = region_manager.get_city_name_by_code(area) or f"未知城市({area})"
            year = year or datetime.now().year
            trend_avg = trend_data.get('avg', 0)
            days_in_year = self._get_days_in_year(year)
            
            return pd.DataFrame({
                '搜索关键词': [keyword],
                '城市': [city_name],
                '城市编号': [area],
                '年份': [year],
                '趋势日均值': [trend_avg],
                '趋势年总值': [trend_avg * days_in_year],
                '爬取时间': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            })
        except Exception as e:
            log.error(f"TrendProcessor error: {e}")
            return pd.DataFrame()

# 单例
search_processor = SearchProcessor()
