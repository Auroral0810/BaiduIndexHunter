"""
资讯指数数据处理器
"""
import pandas as pd
from datetime import datetime, timedelta
from src.core.logger import log

class FeedProcessor:
    """资讯指数数据处理器"""
    
    def process_feed_index_data(self, data, keyword, city_code, city_name, start_date, end_date, decrypted_data, data_type='day'):
        """处理资讯指数数据"""
        try:
            if not data or not data.get('data') or not data['data'].get('index'):
                return None, None
            
            index_data = data['data']['index'][0]
            general_ratio = index_data.get('generalRatio', {})
            avg_value = general_ratio.get('avg', 0)
            yoy_value = general_ratio.get('yoy', '-')
            qoq_value = general_ratio.get('qoq', '-')
            
            api_start_date = index_data.get('startDate', start_date)
            api_end_date = index_data.get('endDate', end_date)
            
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
            
            if data_type == 'week':
                interval, data_frequency = 7, '周度'
                expected_points = (total_days + 6) // 7
            else:
                interval, data_frequency = 1, '日度'
                expected_points = total_days

            if data_length < expected_points:
                values.extend(['0'] * (expected_points - data_length))
                data_length = expected_points

            daily_data = []
            for i in range(expected_points):
                current_date = (start + timedelta(days=i*interval)).strftime('%Y-%m-%d')
                if current_date > api_end_date: break
                daily_data.append({
                    '关键词': keyword, '城市代码': city_code, '城市': city_name,
                    '日期': current_date, '数据类型': data_frequency, '数据间隔(天)': interval,
                    '所属年份': current_date[:4], '资讯指数': values[i] if i < len(values) else '0',
                    '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

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

# 单例
feed_processor = FeedProcessor()
