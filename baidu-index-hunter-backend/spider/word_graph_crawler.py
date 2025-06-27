"""
需求图谱爬虫（关键词关联关系）
"""
import pandas as pd
import requests
import json
import time
from datetime import datetime
import threading
import sys
import os
import json
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.logger import log
from utils.rate_limiter import rate_limiter
from utils.retry_decorator import retry
from utils.cipher_text import cipher_text_generator
from cookie_manager.cookie_rotator import cookie_rotator
from config.settings import BAIDU_INDEX_API
from fake_useragent import UserAgent
ua = UserAgent()
useragent=ua.random#随机生成seragent


cookies = {
    'BDUSS': '1QWW1LZnJFWDVPN350SDV6dWJTZHRNWnhWeEFjSVpPckduLTRMakQyRGhoa1ZvSVFBQUFBJCQAAAAAAAAAAAEAAABGVUcnzOy6o9PAs7oAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOH5HWjh-R1oM2',
    'BAIDUID': 'E8C2F89B2338E88F38F4D0A154FC1B64:SL=0:NR=50:FG=1',
    'HMACCOUNT': 'B14ADDE7C745CD61',
}

# 3. 需求图谱，参数列表：wordlist[]：电脑；datelist：20241117。
# 请求示例和参数如下：
datelist = '20250501'
wordlist = '电脑'
url = f'{BAIDU_INDEX_API["word_graph_url"]}?wordlist[]={wordlist}&datelist={datelist}'
# 'https://index.baidu.com/api/WordGraph/multi?wordlist[]=%E6%89%8B%E6%9C%BA&datelist=20250518'
headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Referer': BAIDU_INDEX_API['referer'],
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': useragent,
    'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
}

response = requests.get(
    url,
    cookies=cookies,
    headers=headers,
)
# 解析需求图谱结果
def parse_word_graph_result(response_json):
    """
    解析百度指数需求图谱API返回的结果
    
    参数:
        response_json: API返回的JSON响应
        
    返回:
        解析后的数据
    """
    try:
        if response_json['status'] == 0:
            data = response_json['data']
            period = data.get('period', '')
            print(f"数据周期: {period}")
            
            for word_item in data.get('wordlist', []):
                keyword = word_item.get('keyword', '')
                print(f"\n关键词: {keyword}")
                
                word_graph = word_item.get('wordGraph', [])
                print(f"相关词数量: {len(word_graph)}")
                
                print("\n所有相关词列表:")
                for i, item in enumerate(word_graph, 1):
                    word = item.get('word', '')
                    pv = item.get('pv', 0)
                    ratio = item.get('ratio', 0)
                    sim = item.get('sim', 0)
                    
                    print(f"{i}. 词: {word}, 搜索量: {pv}, 变化率: {ratio}%, 相关度: {sim}")
                
            return data
        else:
            print(f"请求失败，状态码: {response_json['status']}, 消息: {response_json.get('message', '未知错误')}")
            return None
    except Exception as e:
        print(f"解析需求图谱数据时出错: {e}")
        return None

# 解析响应结果
if response.status_code == 200:
    try:
        result = response.json()
        parse_word_graph_result(result)
    except Exception as e:
        print(f"解析响应JSON时出错: {e}")
else:
    print(f"请求失败，状态码: {response.status_code}")
