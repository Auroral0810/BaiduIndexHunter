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
        region = region_manager.get_region_by_code(region_code)
        return region['name'] if region else f"未知地区({region_code})"

    def _get_province_name(self, prov_code):
        """获取省份名称"""
        # 尝试从 region 表获取（省份也是一种 region）
        region = region_manager.get_region_by_code(prov_code)
        if region:
            return region['name']
        return f"未知省份({prov_code})"

    def _get_city_name(self, city_code):
        """获取城市名称"""
        return region_manager.get_city_name_by_code(city_code) or f"未知城市({city_code})"

    def _parse_period(self, period_str):
        """
        解析时间范围字符串
        格式: "YYYYMMDD|YYYYMMDD" 或 "YYYY-MM-DD|YYYY-MM-DD"
        返回: (start_date, end_date) 格式为 YYYY-MM-DD
        """
        if not period_str:
            return None, None
        
        try:
            parts = period_str.split('|')
            if len(parts) != 2:
                return period_str, period_str
            
            start_str, end_str = parts[0].strip(), parts[1].strip()
            
            # 处理不同格式
            if len(start_str) == 8:  # YYYYMMDD
                start_date = f"{start_str[:4]}-{start_str[4:6]}-{start_str[6:8]}"
            else:
                start_date = start_str
            
            if len(end_str) == 8:  # YYYYMMDD
                end_date = f"{end_str[:4]}-{end_str[4:6]}-{end_str[6:8]}"
            else:
                end_date = end_str
            
            return start_date, end_date
        except Exception as e:
            log.warning(f"Period parse error: {period_str}, {e}")
            return period_str, period_str

    def _merge_real_data(self, dict1, dict2):
        """
        合并两个数据字典（处理 provReal 和 prov_real 等情况）
        """
        if not dict1 and not dict2:
            return {}
        if not dict1:
            return dict2 or {}
        if not dict2:
            return dict1 or {}
        
        merged = dict(dict1)
        for k, v in dict2.items():
            if k not in merged or merged[k] is None:
                merged[k] = v
        return merged

    def _create_empty_region_data(self, keyword, query_region_code, query_region_name, period, data_level):
        """创建空的地域分布数据记录"""
        return pd.DataFrame([{
            '关键词': keyword,
            '查询地区代码': query_region_code,
            '查询地区名称': query_region_name,
            '时间范围': period,
            '数据级别': data_level,
            '代码': '0',
            '名称': '无数据',
            '指数': 0,
            '真实占比': 0.0,
            '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }])

    def process_region_distribution_data(self, data, query_region_code=0, keyword=None, start_date=None, end_date=None):
        """
        处理地域分布数据
        
        参数:
            data: API 返回的原始数据
            query_region_code: 查询的地区代码（0=全国，9xx=省份）
            keyword: 关键词
            start_date: 开始日期
            end_date: 结束日期
            
        返回:
            DataFrame: 处理后的数据
            
        数据结构说明:
            - 选择全国(0): 返回 prov/provReal/prov_real (省份数据) 和 city/cityReal/city_real (TOP城市数据)
            - 选择省份(9xx): 只返回 city/cityReal/city_real (该省份下的城市数据)
        """
        try:
            query_region_name = self._get_region_name(query_region_code)
            default_period = f"{start_date}|{end_date}" if start_date and end_date else ""
            
            if not data or data.get('status') != 0 or 'data' not in data:
                if keyword:
                    return self._create_empty_region_data(keyword, query_region_code, query_region_name, default_period, 'none')
                return pd.DataFrame()
            
            region_data = data['data'].get('region', [])
            # log.info(f"DEBUG_REGION: region_data={region_data}")
            if not region_data:
                if keyword:
                    return self._create_empty_region_data(keyword, query_region_code, query_region_name, default_period, 'none')
                return pd.DataFrame()
            
            results = []
            
            for item in region_data:
                item_keyword = item.get('key', keyword or '')
                
                # 解析时间范围
                period_str = item.get('period', '')
                if period_str:
                    parsed_start, parsed_end = self._parse_period(period_str)
                    period = f"{parsed_start}|{parsed_end}"
                else:
                    period = default_period
                
                # 获取查询地区信息
                area_code = item.get('area', query_region_code)
                area_name = item.get('areaName', query_region_name)
                
                # 处理省份数据（仅当查询全国时有数据）
                # 合并 prov/provReal/prov_real
                prov_data = item.get('prov', {}) or {}
                # log.info(f"DEBUG_REGION: prov_data={prov_data}")
                prov_real_merged = self._merge_real_data(
                    item.get('provReal', {}),
                    item.get('prov_real', {})
                )
                
                # 获取省份映射表，用于名称和所属大区查询
                all_provinces = region_manager.get_all_provinces()
                
                # 处理省份级别数据
                # 重命名变量以避免混淆
                prov_index_map = item.get('prov', {}) or {}
                # log.info(f"DEBUG_REGION: prov_index_map={prov_index_map}")
                prov_real_map = self._merge_real_data(
                    item.get('provReal', {}),
                    item.get('prov_real', {})
                )
                
                region_stats = {}
                if prov_index_map or prov_real_map:
                    # 使用 set set union 确保覆盖所有存在的 code
                    all_prov_codes = set()
                    if prov_index_map:
                        all_prov_codes.update(prov_index_map.keys())
                    if prov_real_map:
                        all_prov_codes.update(prov_real_map.keys())
                        
                    for code in all_prov_codes:  
                        code_str = str(code)
                        # 获取省份信息
                        prov_info = all_provinces.get(code_str)
                        prov_name = prov_info['name'] if prov_info else f"未知省份({code})"
                        
                        # 显式使用 str key 获取值
                        # 注意：如果 user JSON 是正确的，那么 prov_index_map[code_str] 应该是 51 (上海)
                        idx_val = prov_index_map.get(code_str)
                        # log.info(f"DEBUG_REGION: Code {code_str} Name={prov_name} Key={code_str} IndexRaw={idx_val} InIndexMap={code_str in prov_index_map}")
                        # 尝试 int conversion, 只有 explicit None 或者 missing 才会 default 0
                        if idx_val is None:
                            # 尝试用 int key 获取 (防备 keys 是 int)
                            try:
                                idx_val = prov_index_map.get(int(code_str), 0)
                            except:
                                idx_val = 0
                        
                        real_val = prov_real_map.get(code_str)
                        if real_val is None:
                             try:
                                real_val = prov_real_map.get(int(code_str), 0)
                             except:
                                real_val = 0

                        # 确保数值类型
                        try:
                            index_value = int(idx_val)
                        except (ValueError, TypeError):
                            index_value = 0
                        try:
                            real_value = float(real_val)
                        except (ValueError, TypeError):
                            real_value = 0.0
                        
                        results.append({
                            '关键词': item_keyword,
                            '查询地区代码': area_code,
                            '查询地区名称': area_name,
                            '时间范围': period,
                            '数据级别': '省份',
                            '代码': code_str,
                            '名称': prov_name,
                            '指数': index_value,
                            '真实占比': real_value,
                            '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        
                        # 统计大区数据
                        prov_region = prov_info.get('region') if prov_info else None
                        if prov_region:
                            if prov_region not in region_stats:
                                region_stats[prov_region] = {'index': 0, 'real': 0.0}
                            region_stats[prov_region]['index'] += index_value
                            region_stats[prov_region]['real'] += real_value
                
                # 添加大区聚合数据
                for region_name, stats in region_stats.items():
                    results.append({
                        '关键词': item_keyword,
                        '查询地区代码': area_code,
                        '查询地区名称': area_name,
                        '时间范围': period,
                        '数据级别': '区域',
                        '代码': '-',
                        '名称': region_name,
                        '指数': stats['index'],
                        '真实占比': stats['real'],
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                # 处理城市数据
                city_index_map = item.get('city', {}) or {}
                city_real_map = self._merge_real_data(
                    item.get('cityReal', {}),
                    item.get('city_real', {})
                )
                
                # 处理城市级别数据
                if city_index_map or city_real_map:
                    all_city_codes = set()
                    if city_index_map:
                        all_city_codes.update(city_index_map.keys())
                    if city_real_map:
                        all_city_codes.update(city_real_map.keys())

                    for code in all_city_codes:
                        code_str = str(code)
                        
                        idx_val = city_index_map.get(code_str)
                        if idx_val is None:
                             try:
                                idx_val = city_index_map.get(int(code_str), 0)
                             except:
                                idx_val = 0
                        
                        real_val = city_real_map.get(code_str)
                        if real_val is None:
                             try:
                                real_val = city_real_map.get(int(code_str), 0)
                             except:
                                real_val = 0
                        
                        # 确保数值类型
                        try:
                            index_value = int(idx_val)
                        except (ValueError, TypeError):
                            index_value = 0
                        try:
                            real_value = float(real_val)
                        except (ValueError, TypeError):
                            real_value = 0.0
                        
                        results.append({
                            '关键词': item_keyword,
                            '查询地区代码': area_code,
                            '查询地区名称': area_name,
                            '时间范围': period,
                            '数据级别': '地级市',
                            '代码': code_str,
                            '名称': self._get_city_name(code_str),
                            '指数': index_value,
                            '真实占比': real_value,
                            '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
            
            if results:
                return pd.DataFrame(results)
            else:
                return self._create_empty_region_data(keyword, query_region_code, query_region_name, default_period, 'none')
                
        except Exception as e:
            log.error(f"RegionProcessor error: {e}")
            import traceback
            traceback.print_exc()
            if keyword:
                return self._create_empty_region_data(keyword, query_region_code, self._get_region_name(query_region_code), default_period or "", 'none')
            return pd.DataFrame()

# 单例
region_processor = RegionProcessor()
