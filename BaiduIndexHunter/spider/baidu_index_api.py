"""
百度指数API封装模块
"""
import requests
import json
import time
import random
from datetime import datetime, timedelta


import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.settings import BAIDU_INDEX_API, SPIDER_CONFIG
from cookie_manager.cookie_rotator import cookie_rotator
from utils.logger import log
from utils.cipher_text import cipher_text_generator
from utils.rate_limiter import rate_limiter
from utils.retry_decorator import retry
from db.redis_manager import redis_manager
from db.mysql_manager import mysql_manager
from utils.data_processor import data_processor
from fake_useragent import UserAgent


class BaiduIndexAPI:
    """百度指数API封装，提供搜索指数和趋势数据获取接口"""
    
    # 添加静态变量来跟踪是否已经打印过首次请求信息
    _first_request_printed = False
    
    def __init__(self):
        self.ua = UserAgent()
        self.base_headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': BAIDU_INDEX_API['referer'],
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }
        self.search_url = BAIDU_INDEX_API['search_url']
        self.trend_url = BAIDU_INDEX_API['trend_url']
    
    def _get_headers(self, cipher_text=None):
        """
        获取请求头
        :param cipher_text: Cipher-Text值
        :return: 请求头字典
        """
        headers = self.base_headers.copy()
        headers['User-Agent'] = self.ua.random
        
        if cipher_text:
            headers['Cipher-Text'] = cipher_text
            
        return headers
    
    def _parse_cookie_string(self, cookie_string):
        """
        将cookie字符串解析为字典
        :param cookie_string: cookie字符串或字典
        :return: cookie字典
        """
        # 如果已经是字典，直接返回
        if isinstance(cookie_string, dict):
            return cookie_string
            
        # 如果是字符串，尝试解析
        cookie_dict = {}
        if not cookie_string:
            return cookie_dict
            
        # 处理可能的JSON格式
        if isinstance(cookie_string, str):
            if cookie_string.startswith('{') and cookie_string.endswith('}'):
                try:
                    return json.loads(cookie_string)
                except:
                    pass
                    
            # 处理标准cookie字符串格式
            for item in cookie_string.split('; '):
                if '=' in item:
                    name, value = item.split('=', 1)
                    cookie_dict[name] = value
                
        return cookie_dict
        
    @retry(max_retries=SPIDER_CONFIG['retry_times'])
    def get_search_index(self, keyword, area=0, days=30, start_date=None, end_date=None, year=None):
        """
        获取搜索指数数据
        :param keyword: 关键词
        :param area: 地区代码，默认为0（全国）
        :param days: 天数，默认30天
        :param start_date: 开始日期，格式：yyyy-MM-dd
        :param end_date: 结束日期，格式：yyyy-MM-dd
        :param year: 年份，用于数据处理
        :return: 搜索指数数据
        """
        # 获取cookie
        account_id, cookie_dict = cookie_rotator.get_cookie()
        if not account_id or not cookie_dict:
            log.warning("无可用Cookie，等待Cookie解锁...")
            # 等待cookie可用，最多等待30分钟
            if not cookie_rotator.wait_for_available_cookie(timeout=1800):
                log.error("等待Cookie超时，无法获取搜索指数")
                return None
                
            # 再次尝试获取cookie
            account_id, cookie_dict = cookie_rotator.get_cookie()
            if not account_id or not cookie_dict:
                log.error("无法获取可用Cookie，无法获取搜索指数")
                return None
            
        # 确保cookie_dict是字典类型
        if not isinstance(cookie_dict, dict):
            log.error(f"Cookie格式错误，期望dict类型，实际为{type(cookie_dict)}")
            return None
            
        # 构建请求URL和参数
        params = {
            'word': json.dumps([[{"name": keyword, "wordType": 1}]]),
            'area': str(area)
        }
        
        # 如果提供了日期范围，使用日期范围
        if start_date and end_date:
            params['startDate'] = start_date
            params['endDate'] = end_date
        else:
            params['days'] = str(days)
            
        # 生成Cipher-Text
        cipher_url = f"https://index.baidu.com/v2/main/index.html#/trend/{keyword}?words={keyword}"
        cipher_text = cipher_text_generator.generate(cipher_url)
        
        # 构建请求头
        headers = self._get_headers(cipher_text)
            
        # log.info(f"发送搜索指数请求: {keyword} 地区:{area} 年份")
        
        try:
            # 等待适当的时间间隔
            rate_limiter.wait()
            
            # 发送请求
            response = requests.get(
                self.search_url,
                params=params,
                headers=headers,
                cookies=cookie_dict,
                timeout=SPIDER_CONFIG['timeout']
            )
            
            # 检查响应状态
            if response.status_code != 200:
                log.error(f"请求失败，状态码: {response.status_code}")
                return None
                
            # 解析响应数据
            data = response.json()
            
            # 检查是否被封禁
            if data.get('status') == 10001 and data.get('message') == 'request block':
                log.warning(f"获取搜索指数失败: {data.get('message')}")
                # 标记cookie被锁定
                cookie_rotator.report_cookie_status(account_id, False)
                return None
                
            # 检查数据有效性
            if data.get('status') != 0 or 'data' not in data:
                log.warning(f"获取搜索指数失败: {data.get('message', '未知错误')}")
                return None
                
            # 处理数据
            if year is None and start_date:
                year = int(start_date.split('-')[0])
            
            # 使用数据处理器处理数据
            df = data_processor.process_search_index_data(data['data'], area, keyword, year)
            return df
            
        except Exception as e:
            log.error(f"获取搜索指数异常: {str(e)}")
            return None
    
    @retry(max_retries=SPIDER_CONFIG['retry_times'])
    def get_trend_index(self, keyword, area=0, days=30, start_date=None, end_date=None, year=None):
        """
        获取趋势指数数据
        :param keyword: 关键词
        :param area: 地区代码，默认为0（全国）
        :param days: 天数，默认30天
        :param start_date: 开始日期，格式为YYYY-MM-DD
        :param end_date: 结束日期，格式为YYYY-MM-DD
        :param year: 年份，用于数据处理
        :return: 处理后的DataFrame或None
        """
        # 获取Cookie
        account_id, cookie_dict = cookie_rotator.get_cookie()
        if not account_id or not cookie_dict:
            log.warning("无可用Cookie，等待Cookie解锁...")
            # 等待cookie可用，最多等待30分钟
            if not cookie_rotator.wait_for_available_cookie(timeout=1800):
                log.error("等待Cookie超时，无法获取趋势指数")
                return None
                
            # 再次尝试获取cookie
            account_id, cookie_dict = cookie_rotator.get_cookie()
            if not account_id or not cookie_dict:
                log.error("无法获取可用Cookie，无法获取趋势指数")
                return None
        
        # 确保cookie_dict是字典类型
        if not isinstance(cookie_dict, dict):
            log.error(f"Cookie格式错误，期望dict类型，实际为{type(cookie_dict)}")
            return None
        
        # 控制请求频率
        rate_limiter.wait()
        
        try:
            # 构造请求参数
            params = {
                'word': json.dumps([[{"name": keyword, "wordType": 1}]]),
                'area': str(area),
            }
            
            # 如果提供了日期范围，使用日期范围
            if start_date and end_date:
                params['startDate'] = start_date
                params['endDate'] = end_date
            else:
                params['days'] = str(days)
            
            # 生成Cipher-Text
            url_cipher = f'https://index.baidu.com/v2/main/index.html#/trend/{keyword}?words={keyword}'
            cipher_text = cipher_text_generator.generate(url_cipher)
            
            # 获取请求头
            headers = self._get_headers(cipher_text)
            
            # 打印首次请求信息（如果尚未打印）
            if not BaiduIndexAPI._first_request_printed:
                log.info(f"===== 首次请求信息 =====")
                log.info(f"使用的Cookie ID: {account_id}")
                log.info(f"Cookie字典内容: {cookie_dict}")
                log.info(f"Cookie字段数量: {len(cookie_dict)}")
                log.info(f"Cookie字段列表: {', '.join(list(cookie_dict.keys())[:10])}..." if len(cookie_dict) > 10 else ', '.join(cookie_dict.keys()))
                log.info(f"请求URL: {self.trend_url}")
                log.info(f"请求参数: {params}")
                log.info(f"请求头: {headers}")
                BaiduIndexAPI._first_request_printed = True
            
            # 发送请求
            log.info(f"发送趋势指数请求: {keyword} 地区:{area}")
            
            response = requests.get(
                self.trend_url,
                params=params,
                headers=headers,
                cookies=cookie_dict,
                timeout=SPIDER_CONFIG['timeout']
            )
            
            # 解析响应
            data = response.json()
            
            # 检查状态码和响应内容
            if response.status_code == 200:
                status = data.get('status', -1)
                if status == 0 and 'data' in data:
                    log.info(f"成功获取趋势指数数据: {keyword}")
                    cookie_rotator.report_cookie_status(account_id, True)
                    
                    # 处理数据
                    if year is None and start_date:
                        year = int(start_date.split('-')[0])
                    
                    # 使用数据处理器处理数据
                    df = data_processor.process_trend_index_data(data['data'], area, keyword, year)
                    return df
                else:
                    error_msg = data.get('message', '未知错误')
                    log.warning(f"获取趋势指数失败: {error_msg}")
                    
                    # 检查是否是Cookie被锁定
                    if status == 10001 and "request block" in error_msg:
                        log.warning(f"Cookie {account_id} 已被锁定")
                        cookie_rotator.report_cookie_status(account_id, False)
                    
                    return None
            else:
                log.warning(f"获取趋势指数请求失败, 状态码: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            log.error(f"获取趋势指数时发生网络错误: {e}")
            return None
        except Exception as e:
            log.error(f"获取趋势指数时发生未知错误: {e}")
            return None
    
    def test_cookie(self, cookie_value, test_keyword="百度"):
        """
        测试Cookie是否有效
        :param cookie_value: 要测试的Cookie值
        :param test_keyword: 测试用的关键词
        :return: (bool, str) - (是否有效, 失效原因)
        """
        try:
            # 解析cookie字符串为字典
            cookie_dict = self._parse_cookie_string(cookie_value)
            
            # 构造请求参数
            params = {
                'word': json.dumps([[{"name": test_keyword, "wordType": 1}]]),
                'area': '0',
                'days': '30',
            }
            
            # 生成Cipher-Text
            url_cipher = f'https://index.baidu.com/v2/main/index.html#/trend/{test_keyword}?words={test_keyword}'
            cipher_text = cipher_text_generator.generate(url_cipher)
            
            # 获取请求头
            headers = self._get_headers(cipher_text)
            
            # 发送请求
            response = requests.get(
                self.search_url,
                params=params,
                headers=headers,
                cookies=cookie_dict,
                timeout=SPIDER_CONFIG['timeout']
            )
            
            # 解析响应
            data = response.json()
            
            # 检查状态码和响应内容
            if response.status_code == 200:
                status = data.get('status', -1)
                if status == 0 and 'data' in data:
                    return True, ""
                else:
                    error_msg = data.get('message', '未知错误')
                    
                    # 检查是否是Cookie被锁定
                    if status == 10001 and "request block" in error_msg:
                        return False, "Cookie已被锁定"
                    elif status == 10000:
                        return False, "请求参数错误"
                    elif status == 10002:
                        return False, "加密参数错误"
                    else:
                        return False, error_msg
            else:
                return False, f"HTTP错误: {response.status_code}"
                
        except requests.RequestException as e:
            return False, f"网络错误: {str(e)}"
        except Exception as e:
            return False, f"未知错误: {str(e)}"

    def test_case_jinan_computer(self):
        """
        测试用例：获取济南地区'电脑'关键词2017-2018年的指数数据
        """
        # 测试用的cookie
        test_cookie = {
            'BDUSS': '1QWW1LZnJFWDVPN350SDV6dWJTZHRNWnhWeEFjSVpPckduLTRMakQyRGhoa1ZvSVFBQUFBJCQAAAAAAAAAAAEAAABGVUcnzOy6o9PAs7oAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOH5HWjh-R1oM2',
            'BAIDUID': 'E8C2F89B2338E88F38F4D0A154FC1B64:SL=0:NR=50:FG=1',
            'HMACCOUNT': 'B14ADDE7C745CD61',
        }
        
        # 测试参数
        keyword = "电脑"
        area = 1  # 济南
        start_date = "2017-01-01"
        end_date = "2018-12-31"
        
        log.info(f"===== 开始测试用例：济南地区'电脑'关键词2017-2018年指数数据 =====")
        
        # 生成Cipher-Text
        cipher_url = f"https://index.baidu.com/v2/main/index.html#/trend/{keyword}?words={keyword}"
        cipher_text = cipher_text_generator.generate(cipher_url)
        
        # 构建请求头
        headers = self._get_headers(cipher_text)
        
        # 构建请求参数
        params = {
            'word': json.dumps([[{"name": keyword, "wordType": 1}]]),
            'area': str(area),
            'startDate': start_date,
            'endDate': end_date
        }
        
        log.info(f"测试用例请求参数: {params}")
        log.info(f"测试用例Cookie: {test_cookie}")
        
        try:
            # 发送请求
            response = requests.get(
                self.search_url,
                params=params,
                headers=headers,
                cookies=test_cookie,
                timeout=SPIDER_CONFIG['timeout']
            )
            
            # 检查响应状态
            if response.status_code != 200:
                log.error(f"测试用例请求失败，状态码: {response.status_code}")
                return None
                
            # 解析响应数据
            data = response.json()
            
            # 检查数据有效性
            if data.get('status') != 0 or 'data' not in data:
                log.warning(f"测试用例获取数据失败: {data.get('message', '未知错误')}")
                return None
                
            # 处理数据
            year = int(start_date.split('-')[0])
            df = data_processor.process_search_index_data(data['data'], area, keyword, year)
            
            log.info(f"测试用例成功获取数据，数据条数: {len(df) if df is not None else 0}")
            return df
            
        except Exception as e:
            log.error(f"测试用例执行异常: {str(e)}")
            return None


# 创建百度指数API单例
baidu_index_api = BaiduIndexAPI()
# baidu_index_api.test_case_jinan_computer()