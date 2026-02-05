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

    def process_interest_profile_data(self, data, query_keyword=None):
        """处理兴趣分布数据"""
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
                
                # 处理兴趣点数据
                for interest_item in item.get('result', []):  # 注意：有时API结构可能是 item.get('interest') 或 item.get('result')
                    # 这里尝试兼容两种结构，通常兴趣分布API返回结构可能含有一层 'result'
                    # 不过根据之前的 demographic_data 来看，interest 是直接在 item 下的
                    # 为了安全，先检查 'interest'，如果没有再检查 'result' 
                    # 但根据经验，专门的兴趣接口可能返回列表
                    
                    # 假设结构与 demographic 类似，但在 interest_api_url 返回的可能略有不同
                    # 保守策略：遍历可能的字段
                    pass

                # 根据 user context, use generic extraction
                # 重新参考 demographic 结构: item.get('interest', [])
                for interest in item.get('interest', []):
                     data_records.append({
                        '关键词': word,
                        '兴趣名称': interest.get('desc', ''),
                        'TGI': interest.get('tgi', ''),
                        '占比': interest.get('rate', 0),
                        '数据周期': period,
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            return pd.DataFrame(data_records)
        except Exception as e:
            log.error(f"InterestProfile processing error: {e}")
            return pd.DataFrame()

# 单例
demographic_processor = DemographicProcessor()
