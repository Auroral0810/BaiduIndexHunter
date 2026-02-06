"""
资讯指数数据处理器
"""
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
from src.core.logger import log
from src.core.config import BAIDU_INDEX_API

class FeedProcessor:
    """资讯指数数据处理器"""
    
    def _decrypt(self, key, data):
        """解密百度指数数据"""
        if not key or not data:
            return ""
            
        try:
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
        except Exception as e:
            log.error(f"解密数据时出错: {e}")
            return ""

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

    def process_feed_index_data(self, data, cookie, keyword, city_code, city_name, start_date, end_date, decrypted_data, data_type='day'):
        """处理资讯指数数据"""
        try:
            # data.get('data') could be a string '' if status is 1
            res_data = data.get('data', {})
            if isinstance(res_data, dict):
                index_list = res_data.get('index', [])
            else:
                index_list = []
            
            # If index_list is empty, we create a dummy index_item to trigger zero-fill logic
            if not index_list:
                index_item = {}
            else:
                index_item = index_list[0]
            general_ratio = index_item.get('generalRatio', {})
            avg_value = general_ratio.get('avg', 0)
            yoy_value = general_ratio.get('yoy', '-')
            qoq_value = general_ratio.get('qoq', '-')
            
            api_start_date = index_item.get('startDate', start_date)
            api_end_date = index_item.get('endDate', end_date)
            
            start = datetime.strptime(api_start_date, '%Y-%m-%d')
            end = datetime.strptime(api_end_date, '%Y-%m-%d')
            total_days = (end - start).days + 1
            
            # Handle empty decrypted data
            if not decrypted_data or not isinstance(decrypted_data, str) or not decrypted_data.strip():
                interval = 7 if data_type == 'week' else 1
                data_frequency = '周度' if data_type == 'week' else '日度'
                data_length = (total_days + 6) // 7 if data_type == 'week' else total_days
                
                daily_data = []
                for i in range(data_length):
                    current_date = (start + timedelta(days=i*interval)).strftime('%Y-%m-%d')
                    if current_date > api_end_date: break
                    daily_data.append({
                        '关键词': keyword, '城市代码': city_code, '城市': city_name,
                        '日期': current_date, '数据类型': data_frequency, '数据间隔(天)': interval,
                        '所属年份': current_date[:4], '资讯指数': '0',
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                stats_record = {
                    '关键词': keyword, '城市代码': city_code, '城市': city_name,
                    '时间范围': f"{api_start_date} 至 {api_end_date}", '日均值': avg_value,
                    '同比': yoy_value, '环比': qoq_value, '总值': 0,
                    '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                return daily_data, stats_record

            # Handle non-empty data
            raw_values = decrypted_data.split(',')
            values = [v if v.strip() else '0' for v in raw_values]
            data_length = len(values)
            
            if total_days > 366:
                 # Auto-detect weekly for long duration
                 interval, data_frequency = 7, '周度'
                 log.info(f"FeedProcessor: Auto-detect weekly data for {keyword} (Duration > 366 days)")
            else:
                interval, data_frequency = 1, '日度'
                log.info(f"FeedProcessor: Detect daily data for {keyword} (Duration <= 366 days)")

            daily_data = []
            
            # 使用 while 循环严格按照日期范围生成数据
            curr_date_obj = start
            idx = 0
            
            while curr_date_obj <= end:
                current_date = curr_date_obj.strftime('%Y-%m-%d')
                if current_date > api_end_date: break
                
                # 获取值，不够补0
                val = values[idx] if idx < len(values) else '0'
                
                daily_data.append({
                    '关键词': keyword, '城市代码': city_code, '城市': city_name,
                    '日期': current_date, '数据类型': data_frequency, '数据间隔(天)': interval,
                    '所属年份': current_date[:4], '资讯指数': val,
                    '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
                # Debug log for the first processed point
                if idx == 0:
                    log.debug(f"关键词 '{keyword}' (城市 {city_code}) 第一个处理点: 日期={current_date}, 值={val}")
                
                curr_date_obj += timedelta(days=interval)
                idx += 1

            total_value = sum(int(v) for v in values if v.isdigit())
            stats_record = {
                '关键词': keyword, '城市代码': city_code, '城市': city_name,
                '时间范围': f"{api_start_date} 至 {api_end_date}", '日均值': avg_value,
                '同比': yoy_value, '环比': qoq_value, '总值': total_value,
                '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            return daily_data, stats_record
        except Exception as e:
            log.error(f"FeedProcessor error: {e}")
            return None, None

    def process_multi_feed_index_data(self, data, cookie, keywords, city_code, city_name, start_date, end_date):
        """处理多个关键词的资讯指数数据"""
        if not data or (not data.get('data') and data.get('status') != 1):
            log.warning(f"数据为空或格式不正确: {data}")
            return [], []
            
        try:
            res_data = data.get('data', {})
            # If res_data is a string (e.g., status 1 results in data: ''), treat it as no uniqid
            uniqid = res_data.get('uniqid') if isinstance(res_data, dict) else None
            
            # Handle status 1 (no data) or missing uniqid
            if data.get('status') == 1 or not uniqid:
                log.info("API returned status 1 or no uniqid, generating zero-filled records.")
                all_daily_data = []
                all_stats_records = []
                for keyword in keywords:
                    daily, stats = self.process_feed_index_data(
                        data, cookie, keyword, city_code, city_name, 
                        start_date, end_date, "", 'day'
                    )
                    if daily: all_daily_data.extend(daily)
                    if stats: all_stats_records.append(stats)
                return all_daily_data, all_stats_records
                
            # 获取解密密钥
            key = self._get_key(uniqid, cookie)
            log.info(f"获取到解密密钥: {key}")
            
            if not key:
                log.error("无法获取解密密钥，停止处理")
                return [], []
                
            all_daily_data = []
            all_stats_records = []
            
            index_list = res_data.get('index', [])
            
            # 处理每个关键词的数据
            for i, keyword in enumerate(keywords):
                try:
                    index_item = index_list[i] if i < len(index_list) else {}
                    raw_data = index_item.get('data', '')
                    data_type = index_item.get('type', 'day')
                    
                    log.info(f"正在为关键词 '{keyword}' 解密数据. Key: {key}")
                    log.info(f"原始加密数据: {raw_data[:100]}...")
                    
                    # 解密数据
                    decrypted_data = self._decrypt(key, raw_data)
                    log.info(f"关键词 '{keyword}' (城市 {city_code}) 解密后的数据: {decrypted_data[:100]}...")
                    
                    # 验证解密结果
                    if decrypted_data and ',' not in decrypted_data and len(decrypted_data) > 0:
                        log.warning(f"警告: 关键词 '{keyword}' 的解密结果中不包含逗号，可能解密失败")

                    # 创建单个关键词的临时数据结构
                    single_data = {
                        'data': {
                            'index': [index_item],
                            'uniqid': uniqid
                        },
                        'status': 0
                    }
                    
                    # 调用单个处理逻辑
                    daily_data, stats_record = self.process_feed_index_data(
                        single_data, cookie, keyword, city_code, city_name, 
                        start_date, end_date, decrypted_data, data_type
                    )
                    
                    if daily_data:
                        all_daily_data.extend(daily_data)
                    if stats_record:
                        all_stats_records.append(stats_record)
                        
                except Exception as e:
                    log.error(f"处理关键词 '{keyword}' 时出错: {e}")
                    
            return all_daily_data, all_stats_records
            
        except Exception as e:
            log.error(f"process_multi_feed_index_data error: {e}")
            return [], []

# 单例
feed_processor = FeedProcessor()
