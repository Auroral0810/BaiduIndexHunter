"""
人群属性数据处理器
"""
import pandas as pd
from datetime import datetime
from src.core.logger import log

class DemographicProcessor:
    """人群属性数据处理器"""
    
    def process_demographic_data(self, data, query_keyword=None):
        """
        处理人群属性数据 (baseAttributes API)
        
        API返回格式:
        {
            "status": 0,
            "data": {
                "result": [
                    {
                        "word": "手机",
                        "gender": [{"typeId": 0, "desc": "女", "tgi": 89.2, "rate": 41.08}, ...],
                        "age": [{"typeId": 1, "desc": "0-19", "tgi": 111.67, "rate": 7.39}, ...]
                    }
                ],
                "startDate": "2026-01-01",
                "endDate": "2026-01-31"
            }
        }
        """
        try:
            if not data or data.get('status') != 0:
                log.warning(f"[DemographicProcessor] Invalid data or status != 0")
                return pd.DataFrame()
            
            api_data = data.get('data', {})
            result = api_data.get('result', [])
            start_date = api_data.get('startDate', '')
            end_date = api_data.get('endDate', '')
            period = f"{start_date} 至 {end_date}" if start_date and end_date else ''
            
            data_records = []
            crawl_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for item in result:
                word = item.get('word', query_keyword or '')
                
                # 处理性别数据
                for gender_item in item.get('gender', []):
                    tgi_val = gender_item.get('tgi', '')
                    # TGI 可能为空字符串，需要处理
                    tgi_display = tgi_val if tgi_val != '' else '-'
                    data_records.append({
                        '关键词': word,
                        '属性类型': '性别',
                        '属性值': gender_item.get('desc', ''),
                        '比例': gender_item.get('rate', 0),
                        'TGI': tgi_display,
                        '数据周期': period,
                        '爬取时间': crawl_time
                    })
                
                # 处理年龄数据
                for age_item in item.get('age', []):
                    tgi_val = age_item.get('tgi', '')
                    tgi_display = tgi_val if tgi_val != '' else '-'
                    data_records.append({
                        '关键词': word,
                        '属性类型': '年龄',
                        '属性值': age_item.get('desc', ''),  # 已经是 "0-19", "20-29" 格式
                        '比例': age_item.get('rate', 0),
                        'TGI': tgi_display,
                        '数据周期': period,
                        '爬取时间': crawl_time
                    })
            
            log.info(f"[DemographicProcessor] Processed {len(data_records)} records")
            return pd.DataFrame(data_records)
            
        except Exception as e:
            log.error(f"DemographicProcessor error: {e}")
            return pd.DataFrame()

    def process_interest_profile_data(self, data, query_keyword=None):
        """
        处理兴趣分布数据 (interest API)
        
        API返回格式与 baseAttributes 类似，但包含 interest 字段
        {
            "status": 0,
            "data": {
                "result": [
                    {
                        "word": "手机",
                        "interest": [{"typeId": 1, "desc": "科技数码", "tgi": 150.5, "rate": 25.3}, ...]
                    }
                ],
                "startDate": "2026-01-01",
                "endDate": "2026-01-31"
            }
        }
        """
        try:
            if not data or data.get('status') != 0:
                log.warning(f"[InterestProcessor] Invalid data or status != 0")
                return pd.DataFrame()
            
            api_data = data.get('data', {})
            result = api_data.get('result', [])
            start_date = api_data.get('startDate', '')
            end_date = api_data.get('endDate', '')
            period = f"{start_date} 至 {end_date}" if start_date and end_date else ''
            
            data_records = []
            crawl_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for item in result:
                word = item.get('word', query_keyword or '')
                
                # 处理兴趣数据
                for interest_item in item.get('interest', []):
                    tgi_val = interest_item.get('tgi', '')
                    tgi_display = tgi_val if tgi_val != '' else '-'
                    data_records.append({
                        '关键词': word,
                        '兴趣名称': interest_item.get('desc', ''),
                        'TGI': tgi_display,
                        '占比': interest_item.get('rate', 0),
                        '数据周期': period,
                        '爬取时间': crawl_time
                    })
            
            log.info(f"[InterestProcessor] Processed {len(data_records)} records")
            return pd.DataFrame(data_records)
            
        except Exception as e:
            log.error(f"InterestProfile processing error: {e}")
            return pd.DataFrame()

# 单例
demographic_processor = DemographicProcessor()

