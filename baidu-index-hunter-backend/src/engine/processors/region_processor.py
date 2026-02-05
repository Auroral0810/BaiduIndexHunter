"""
地域分布数据处理器
"""
import pandas as pd
from datetime import datetime
from src.core.logger import log
from src.services.region_service import get_region_manager

region_manager = get_region_manager()

class RegionProcessor:
    """地域分布数据处理器"""
    
    def _get_region_name(self, region_code):
        """获取地区名称"""
        if str(region_code) == '0': return "全国"
        return region_manager.get_region_name_by_code(region_code) or f"未知地区({region_code})"

    def _get_province_name(self, prov_code):
        """获取省份名称"""
        return region_manager.get_province_name_by_code(prov_code) or f"未知省份({prov_code})"

    def _create_empty_region_data(self, keyword, region_code, start_date, end_date=None):
        """创建空的地域分布数据记录"""
        period = f"{start_date}|{end_date}" if end_date else start_date
        return pd.DataFrame([{
            '关键词': keyword,
            '地区代码': region_code,
            '地区名称': self._get_region_name(region_code),
            '时间范围': period,
            '地区级别': 'none',
            '地区代码（具体）': '0',
            '地区名称（具体）': '无数据',
            '指数': 0,
            '占比': 0.0,
            '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }])

    def process_region_distribution_data(self, data, region_code=0, keyword=None, start_date=None, end_date=None):
        """处理地域分布数据"""
        try:
            if not data or data.get('status') != 0 or 'data' not in data:
                if keyword and start_date:
                    return self._create_empty_region_data(keyword, region_code, start_date, end_date)
                return pd.DataFrame()
            
            region_data = data['data'].get('region', [])
            if not region_data:
                if keyword and start_date:
                    return self._create_empty_region_data(keyword, region_code, start_date, end_date)
                return pd.DataFrame()
            
            results = []
            for item in region_data:
                item_keyword = item.get('key', keyword or '')
                period = item.get('period', f"{start_date}|{end_date}" if start_date and end_date else start_date)
                area_name = item.get('areaName', self._get_region_name(region_code))
                
                # Helper to process geo levels
                def process_geo(geo_dict, real_dict, level):
                    all_codes = set(geo_dict.keys()) | set(real_dict.keys())
                    for code in all_codes:
                        name = self._get_province_name(code) if level == 'province' else (region_manager.get_city_name_by_code(code) or f"未知城市({code})")
                        results.append({
                            '关键词': item_keyword,
                            '地区代码': region_code,
                            '地区名称': area_name,
                            '时间范围': period,
                            '地区级别': level,
                            '地区代码（具体）': code,
                            '地区名称（具体）': name,
                            '指数': geo_dict.get(code, 0),
                            '占比': float(real_dict.get(code, 0.0) or 0.0),
                            '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })

                process_geo(item.get('prov', {}), item.get('provReal', {}) or item.get('prov_real', {}), 'province')
                process_geo(item.get('city', {}), item.get('cityReal', {}) or item.get('city_real', {}), 'city')
            
            return pd.DataFrame(results) if results else self._create_empty_region_data(keyword, region_code, start_date, end_date)
        except Exception as e:
            log.error(f"RegionProcessor error: {e}")
            return self._create_empty_region_data(keyword, region_code, start_date, end_date) if keyword and start_date else pd.DataFrame()

# 单例
region_processor = RegionProcessor()
