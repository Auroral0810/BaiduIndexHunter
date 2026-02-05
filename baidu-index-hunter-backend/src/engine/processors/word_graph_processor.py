"""
需求图谱数据处理器
"""
import pandas as pd
from datetime import datetime
from src.core.logger import log

class WordGraphProcessor:
    """需求图谱数据处理器"""
    
    def process_word_graph_data(self, data, keyword, datelist):
        """处理需求图谱数据"""
        try:
            if not data or data.get('status') != 0 or 'data' not in data:
                return pd.DataFrame()
            
            api_data = data['data']
            period_raw = api_data.get('period', '')
            
            # Format period string
            if '|' in period_raw:
                try:
                    p_start, p_end = period_raw.split('|')
                    period = f"{p_start[:4]}-{p_start[4:6]}-{p_start[6:]}-{p_end[:4]}-{p_end[4:6]}-{p_end[6:]}"
                except:
                    period = period_raw
            else:
                period = period_raw
            
            results = []
            for word_item in api_data.get('wordlist', []):
                item_keyword = word_item.get('keyword', keyword)
                word_graph = word_item.get('wordGraph', [])
                
                if not word_graph:
                    results.append({
                        '关键词': item_keyword, '相关词': '', '搜索量': 0,
                        '变化率': 0, '相关度': 0, '数据周期': period,
                        '日期': datelist, '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    continue
                
                for item in word_graph:
                    results.append({
                        '关键词': item_keyword,
                        '相关词': item.get('word', ''),
                        '搜索量': item.get('pv', 0),
                        '变化率': item.get('ratio', 0),
                        '相关度': item.get('sim', 0),
                        '数据周期': period,
                        '日期': datelist,
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            return pd.DataFrame(results)
        except Exception as e:
            log.error(f"WordGraphProcessor error: {e}")
            return pd.DataFrame()

# 单例
word_graph_processor = WordGraphProcessor()
