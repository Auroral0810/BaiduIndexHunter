"""
搜索指数与趋势指数处理器
"""
import pandas as pd
import requests
from datetime import datetime, timedelta
from src.core.logger import log
from src.core.config import BAIDU_INDEX_API
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
            res_data = data.get('data', {})
            general_ratio_list = res_data.get('generalRatio', [])
            if not general_ratio_list:
                return pd.DataFrame()
            general_ratio = general_ratio_list[0]
            
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
            res_data = data.get('data', {})
            trend_list = res_data.get('index', [])
            if not trend_list:
                return pd.DataFrame()
            trend_data = trend_list[0]
            
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

    def process_search_index_daily_data(self, data, cookie, keyword, city_code, city_name, 
                                       start_date, end_date, decrypted_all, decrypted_wise, decrypted_pc):
        """
        处理搜索指数日度详细数据与统计摘要
        :return: (daily_data_list, stats_record)
        """
        try:
            # 1. 处理日度列表
            all_list = decrypted_all.split(',') if decrypted_all else []
            wise_list = decrypted_wise.split(',') if decrypted_wise else []
            pc_list = decrypted_pc.split(',') if decrypted_pc else []
            
            # 计算日期列表
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            delta = end_dt - start_dt
            expected_days = delta.days + 1
            
            # 规则: 跨度超过366天（考虑到闰年），强制认为周度；否则认为日度
            if expected_days > 366:
                interval_days = 7
                data_type = '周度'
                log.info(f"Detect weekly data for {keyword} (Duration > 366 days). Range: {expected_days} days")
            else:
                # 即使数据点少，只要是一年内（含闰年），也强制认为是日度（根据用户要求，可能是缺失数据需要补0）
                interval_days = 1
                data_type = '日度'
                log.info(f"Detect daily data for {keyword} (Duration <= 366 days). Range: {expected_days} days")
            
            daily_data = []
            
            # 使用 while 循环严格按照日期范围生成数据
            curr_date_obj = start_dt
            idx = 0
            
            while curr_date_obj <= end_dt:
                curr_date = curr_date_obj.strftime('%Y-%m-%d')
                
                # 获取数据值，如果超出范围则补0
                val_all = all_list[idx] if idx < len(all_list) else '0'
                val_wise = wise_list[idx] if idx < len(wise_list) else '0'
                val_pc = pc_list[idx] if idx < len(pc_list) else '0'
                
                daily_data.append({
                    '关键词': keyword,
                    '城市代码': city_code,
                    '城市': city_name,
                    '日期': curr_date,
                    '数据类型': data_type,
                    '数据间隔(天)': interval_days,
                    '所属年份': curr_date[:4],
                    'PC+移动指数': val_all,
                    '移动指数': val_wise,
                    'PC指数': val_pc,
                    '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
                # 更新日期和索引
                curr_date_obj += timedelta(days=interval_days)
                idx += 1
            
            # 2. 处理统计摘要 (从 generalRatio 获取)
            # 注意: 如果 data 为空，我们可能需要根据 daily_data 手动计算摘要
            ratio_data = data.get('data', {}).get('generalRatio', [{}])[0]
            
            def get_val(terminal, key):
                val = ratio_data.get(terminal, {}).get(key, 0)
                return val if val is not None else 0

            # 统计值计算需注意：如果是周度，总值计算可能需要调整？
            # 百度指数的avg通常是日均值。
            # 总值 = 日均值 * 天数。
            # 这里保持原逻辑：Total = avg * total_days_in_range
            
            stats_record = {
                '关键词': keyword,
                '城市代码': city_code,
                '城市': city_name,
                '时间范围': f"{start_date} 至 {end_date}",
                '整体日均值': get_val('all', 'avg'),
                '整体同比': ratio_data.get('all', {}).get('yoy', '-'),
                '整体环比': ratio_data.get('all', {}).get('qoq', '-'),
                '移动日均值': get_val('wise', 'avg'),
                '移动同比': ratio_data.get('wise', {}).get('yoy', '-'),
                '移动环比': ratio_data.get('wise', {}).get('qoq', '-'),
                'PC日均值': get_val('pc', 'avg'),
                'PC同比': ratio_data.get('pc', {}).get('yoy', '-'),
                'PC环比': ratio_data.get('pc', {}).get('qoq', '-'),
                '整体总值': get_val('all', 'avg') * expected_days,
                '移动总值': get_val('wise', 'avg') * expected_days,
                'PC总值': get_val('pc', 'avg') * expected_days,
                '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return daily_data, stats_record
            
        except Exception as e:
            log.error(f"process_search_index_daily_data error: {e}")
            return [], {}

    def _decrypt(self, key, data):
        """解密百度指数数据"""
        if not key or not data:
            return ""
            
        i = list(key)
        n = list(data)
        a = {}
        r = []
        
        # 构建映射字典
        for A in range(len(i) // 2):
            a[i[A]] = i[len(i) // 2 + A]
        
        # 根据映射解密数据
        for o in range(len(n)):
            r.append(a.get(n[o], n[o]))
        
        return ''.join(r)

    def _get_key(self, uniqid, cookie):
        """从百度接口获取解密密钥"""
        params = {'uniqid': uniqid}
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://index.baidu.com/v2/main/index.html',
            'User-Agent': BAIDU_INDEX_API['user_agent'],
        }
        try:
            response = requests.get(
                'https://index.baidu.com/Interface/ptbk', 
                params=params, 
                cookies=cookie, 
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                res_json = response.json()
                if res_json.get('status') == 0:
                    return res_json.get('data')
            log.error(f"获取解密密钥失败: {response.status_code}, {response.text}")
            return None
        except Exception as e:
            log.error(f"获取解密密钥异常: {e}")
            return None

    def process_multi_search_index_data(self, data, cookie, keywords, city_code, city_name, start_date, end_date):
        """
        处理多个关键词的搜索指数数据
        :param data: API返回的原始数据
        :param cookie: 用于请求的cookie
        :param keywords: 关键词列表
        :param city_code: 城市代码
        :param city_name: 城市名称
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: (daily_data_list, stats_record_list) 元组
        """
        if not data or not data.get('data') or not data['data'].get('userIndexes'):
            log.warning(f"数据为空或格式不正确: {data}")
            return [], []
            
        try:
            res_data = data.get('data', {})
            uniqid = res_data.get('uniqid')
            if not uniqid:
                log.error("API响应中缺少uniqid")
                return [], []
                
            # 获取解密密钥
            key = self._get_key(uniqid, cookie)
            if not key:
                log.error("无法获取解密密钥，停止处理")
                return [], []
                
            # 用于存储每个关键词的处理结果
            all_daily_data = []
            all_stats_records = []
            
            # 确保用户索引和关键词列表长度一致
            user_indexes = res_data.get('userIndexes', [])
            general_ratio = res_data.get('generalRatio', [])
            
            # 处理每个关键词的数据
            for i, keyword in enumerate(keywords):
                try:
                    # 获取各终端数据
                    user_idx = user_indexes[i] if i < len(user_indexes) else {'all': {'data': []}, 'wise': {'data': []}, 'pc': {'data': []}}
                    ratio_idx = general_ratio[i] if i < len(general_ratio) else {'status': 0, 'all': 0, 'pc': 0, 'wise': 0}
                    
                    all_data = user_idx['all']['data'] if 'all' in user_idx and 'data' in user_idx['all'] else ''
                    wise_data = user_idx['wise']['data'] if 'wise' in user_idx and 'data' in user_idx['wise'] else ''
                    pc_data = user_idx['pc']['data'] if 'pc' in user_idx and 'data' in user_idx['pc'] else ''
                    
                    log.info(f"Decrypting data for word: {keyword}. Key: {key}")
                    log.debug(f"Raw encrypted data - All: {all_data[:50]}...")
                    
                    # 解密数据
                    decrypted_all = self._decrypt(key, all_data)
                    decrypted_wise = self._decrypt(key, wise_data)
                    decrypted_pc = self._decrypt(key, pc_data)
                    
                    log.debug(f"Decrypted data - All: {decrypted_all[:50]}...")
                    
                    # 创建单个关键词的临时数据结构
                    single_data = {
                        'data': {
                            'userIndexes': [user_idx],
                            'generalRatio': [ratio_idx],
                            'uniqid': uniqid
                        },
                        'status': 0
                    }
                    
                    # 调用单个处理逻辑
                    daily_data, stats_record = self.process_search_index_daily_data(
                        single_data, cookie, keyword, city_code, city_name, 
                        start_date, end_date, decrypted_all, decrypted_wise, decrypted_pc
                    )
                    
                    if daily_data:
                        all_daily_data.extend(daily_data)
                    if stats_record:
                        all_stats_records.append(stats_record)
                        
                except Exception as e:
                    log.error(f"处理关键词 '{keyword}' 时出错: {e}")
                    
            return all_daily_data, all_stats_records
            
        except Exception as e:
            log.error(f"process_multi_search_index_data error: {e}")
            return [], []

# 单例
search_processor = SearchProcessor()
