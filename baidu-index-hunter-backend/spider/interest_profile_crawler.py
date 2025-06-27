"""
兴趣分布爬虫（人群兴趣画像）
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


# 6.人群画像中的兴趣分布，只有多关键词参数，没有时间可选
# 请求示例和参数如下：

wordlist = ['电脑', '衣服', '手机']
typeid = 29000000 # 兴趣分布
url = f'{BAIDU_INDEX_API["interest_api_url"]}?wordlist[]={wordlist[0]}&wordlist[]={wordlist[1]}&wordlist[]={wordlist[2]}&typeid={typeid}'
# 'https://index.baidu.com/api/SocialApi/interest?wordlist[]=%E7%94%B5%E8%84%91&wordlist[]=%E8%A1%A3%E6%9C%8D&wordlist[]=%E6%89%8B%E6%9C%BA&typeid=29000000'
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

# 解析兴趣分布数据
def parse_interest_data(response_json):
    try:
        if response_json['status'] == 0:
            data = response_json.get('data', {})
            result = data.get('result', [])
            start_date = data.get('startDate', '')
            end_date = data.get('endDate', '')
            
            print(f"数据周期: {start_date} 至 {end_date}")
            
            # 遍历每个关键词的数据
            for item in result:
                word = item.get('word', '')
                print(f"\n关键词: {word}")
                
                # 兴趣分布
                interest_data = item.get('interest', [])
                print("\n兴趣分布:")
                for interest in interest_data:
                    desc = interest.get('desc', '')
                    tgi = interest.get('tgi', '')
                    rate = interest.get('rate', 0)
                    type_id = interest.get('typeId', '')
                    
                    tgi_str = f"TGI: {tgi}" if tgi else "TGI: -"
                    print(f"{desc}: {rate}%, {tgi_str}, 类型ID: {type_id}")
            
            return data
        else:
            print(f"请求失败，状态码: {response_json['status']}, 消息: {response_json.get('message', '未知错误')}")
            return None
    except Exception as e:
        print(f"解析兴趣分布数据时出错: {e}")
        return None

# 解析响应结果
if response.status_code == 200:
    try:
        result = response.json()
        parse_interest_data(result)
    except Exception as e:
        print(f"解析响应JSON时出错: {e}")
else:
    print(f"请求失败，状态码: {response.status_code}")
