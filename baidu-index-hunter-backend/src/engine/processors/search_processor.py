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
            
            daily_data = []
            for i in range(delta.days + 1):
                curr_date = (start_dt + timedelta(days=i)).strftime('%Y-%m-%d')
                daily_data.append({
                    '关键词': keyword,
                    '城市代码': city_code,
                    '城市': city_name,
                    '日期': curr_date,
                    '数据类型': '日度',
                    '数据间隔(天)': 1,
                    '所属年份': curr_date[:4],
                    'PC+移动指数': all_list[i] if i < len(all_list) else '0',
                    '移动指数': wise_list[i] if i < len(wise_list) else '0',
                    'PC指数': pc_list[i] if i < len(pc_list) else '0',
                    '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # 2. 处理统计摘要 (从 generalRatio 获取)
            # 注意: 如果 data 为空，我们可能需要根据 daily_data 手动计算摘要
            ratio_data = data.get('data', {}).get('generalRatio', [{}])[0]
            
            def get_val(terminal, key):
                val = ratio_data.get(terminal, {}).get(key, 0)
                return val if val is not None else 0

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
                '整体总值': get_val('all', 'avg') * (delta.days + 1),
                '移动总值': get_val('wise', 'avg') * (delta.days + 1),
                'PC总值': get_val('pc', 'avg') * (delta.days + 1),
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
            uniqid = data['data']['uniqid']
            # 获取解密密钥
            key = self._get_key(uniqid, cookie)
            if not key:
                log.error("无法获取解密密钥，停止处理")
                return [], []
                
            # 用于存储每个关键词的处理结果
            all_daily_data = []
            all_stats_records = []
            
            # 确保用户索引和关键词列表长度一致
            user_indexes = data['data']['userIndexes']
            general_ratio = data['data']['generalRatio']
            
            # 处理每个关键词的数据
            for i, keyword in enumerate(keywords):
                try:
                    # 获取各终端数据
                    user_idx = user_indexes[i] if i < len(user_indexes) else {'all': {'data': []}, 'wise': {'data': []}, 'pc': {'data': []}}
                    ratio_idx = general_ratio[i] if i < len(general_ratio) else {'status': 0, 'all': 0, 'pc': 0, 'wise': 0}
                    
                    all_data = user_idx['all']['data'] if 'all' in user_idx and 'data' in user_idx['all'] else ''
                    wise_data = user_idx['wise']['data'] if 'wise' in user_idx and 'data' in user_idx['wise'] else ''
                    pc_data = user_idx['pc']['data'] if 'pc' in user_idx and 'data' in user_idx['pc'] else ''
                    
                    # 解密数据
                    decrypted_all = self._decrypt(key, all_data)
                    decrypted_wise = self._decrypt(key, wise_data)
                    decrypted_pc = self._decrypt(key, pc_data)
                    
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
