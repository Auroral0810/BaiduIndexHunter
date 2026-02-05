"""
人群属性数据处理器
"""
import pandas as pd
from datetime import datetime
from src.core.logger import log

class DemographicProcessor:
    """人群属性数据处理器"""
    
    def process_demographic_data(self, data, query_keyword=None):
        """处理人群属性数据"""
        try:
            if not data or data.get('status') != 0:
                return pd.DataFrame()
            
            api_data = data.get('data', {})
            result = api_data.get('result', [])
            start_date = api_data.get('startDate', '')
            end_date = api_data.get('endDate', '')
            period = f"{start_date} 至 {end_date}"
            
            data_records = []
            for item in result:
                word = item.get('word', query_keyword)
                
                # Helper to process child attributes
                def extract_attr(attr_list, attr_type):
                    for attr in attr_list:
                        data_records.append({
                            '关键词': word,
                            '属性类型': attr_type,
                            '属性值': f"{attr.get('desc', '')}岁" if attr_type == '年龄' else attr.get('desc', ''),
                            '比例': attr.get('rate', 0),
                            'TGI': attr.get('tgi', ''),
                            '数据周期': period,
                            '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })

                extract_attr(item.get('gender', []), '性别')
                extract_attr(item.get('age', []), '年龄')
                extract_attr(item.get('education', []), '学历')
                extract_attr(item.get('interest', []), '兴趣')
            
            return pd.DataFrame(data_records)
        except Exception as e:
            log.error(f"DemographicProcessor error: {e}")
            return pd.DataFrame()

# 单例
demographic_processor = DemographicProcessor()
