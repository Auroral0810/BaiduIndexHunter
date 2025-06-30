"""
百度指数API模块
"""
import requests
import json
import time
from datetime import datetime
import threading
from utils.logger import log
from utils.rate_limiter import rate_limiter
from utils.retry_decorator import retry
from utils.cipher_text import cipher_text_generator
from cookie_manager.cookie_rotator import cookie_rotator
from config.settings import BAIDU_INDEX_API


class BaiduIndexAPI:
    """百度指数API封装类，提供对百度指数API的访问方法"""
    
    def __init__(self):
        self.search_url = BAIDU_INDEX_API['search_url']
        self.trend_url = BAIDU_INDEX_API['trend_url']
        self.referer = BAIDU_INDEX_API['referer']
        self.user_agent = BAIDU_INDEX_API['user_agent']
        self.base_headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': self.referer,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': self.user_agent,
            'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }
        self.lock = threading.RLock()
    
    @retry(max_retries=2)
    def get_search_index(self, keyword, area=0, start_date=None, end_date=None):
        """
        获取搜索指数数据
        :param keyword: 关键词
        :param area: 地区代码，默认为0（全国）
        :param start_date: 开始日期，格式：'yyyy-MM-dd'，默认为当年1月1日
        :param end_date: 结束日期，格式：'yyyy-MM-dd'，默认为当年最后一天
        :return: 搜索指数数据字典或None（请求失败）
        """
        try:
            # 如果未指定日期，使用当前年份的时间范围
            current_year = datetime.now().year
            if not start_date:
                start_date = f"{current_year}-01-01"
            if not end_date:
                if current_year == 2025:
                    end_date = "2025-06-23"  # 2025年只到6月23日
                else:
                    end_date = f"{current_year}-12-31"
            
            # 获取一个可用的cookie
            account_id, cookie_dict = cookie_rotator.get_cookie()
            if not cookie_dict:
                # 检查是否有可用cookie，如果有则立即使用，不等待
                available_count = cookie_rotator.get_status().get('available', 0)
                if available_count > 0:
                    log.info(f"检测到有 {available_count} 个可用Cookie，立即重新获取")
                    account_id, cookie_dict = cookie_rotator.get_cookie()
                    if cookie_dict:
                        log.info(f"成功获取到可用Cookie: {account_id}")
                    else:
                        log.warning(f"尽管显示有可用Cookie，但获取失败")
                
                # 如果仍然没有获取到cookie，等待短暂时间后重试
                if not cookie_dict:
                    log.info(f"get_search_index 等待Cookie可用...")
                    # 等待有可用的cookie (最多等待5秒，减少等待时间)
                    if cookie_rotator.wait_for_available_cookie(timeout=5):
                        # 重新尝试获取cookie
                        account_id, cookie_dict = cookie_rotator.get_cookie()
                        if not cookie_dict:
                            log.warning(f"get_search_index 等待Cookie超时，跳过等待继续尝试")
                            return None
                    else:
                        log.warning(f"get_search_index 等待Cookie超时，跳过等待继续尝试")
                        return None
            
            # 构建请求URL
            encoded_keyword = keyword.replace(' ', '%20')
            url = f'{self.search_url}?area={area}&word=[[{{"name":"{encoded_keyword}","wordType":1}}]]&startDate={start_date}&endDate={end_date}'
            
            # 生成Cipher-Text参数
            cipher_url = f'{self.referer}#/trend/{encoded_keyword}?words={encoded_keyword}'
            cipher_text = cipher_text_generator.generate(cipher_url)
            
            if not cipher_text:
                return None
            
            # 构建请求头
            headers = self.base_headers.copy()
            headers['Cipher-Text'] = cipher_text
            
            # 频率控制
            rate_limiter.wait()
            
            # 发送请求
            response = requests.get(
                url=url,
                headers=headers,
                cookies=cookie_dict,
                timeout=15
            )
            
            # 检查响应状态
            if response.status_code != 200:
                # 超时或网络错误不锁定Cookie
                if 'timeout' in str(response).lower() or 'connection' in str(response).lower():
                    return None
                else:
                    cookie_rotator.report_cookie_status(account_id, False)
                    return None
            
            # 解析响应内容
            result = response.json()
            
            # 检查API返回的状态码
            if result.get('status') != 0:
                error_msg = result.get('message', '未知错误')
                
                # 如果是"not login"错误，将cookie标记为永久封禁
                if error_msg == "not login":
                    cookie_rotator.report_cookie_status(account_id, False, permanent=True)
                    
                    # 检查是否有可用cookie，如果有则立即使用，不等待
                    available_count = cookie_rotator.get_status().get('available', 0)
                    if available_count > 0:
                        log.info(f"检测到有 {available_count} 个可用Cookie，立即重新获取")
                        return self.get_search_index(keyword, area, start_date, end_date)
                    
                    # 等待看是否有其他可用Cookie
                    if cookie_rotator.wait_for_available_cookie(timeout=5):
                        # 递归调用自身重试
                        return self.get_search_index(keyword, area, start_date, end_date)
                    return None
                # 如果是请求频率限制错误（状态码10001），临时锁定cookie
                elif result.get('status') == 10001:
                    cookie_rotator.report_cookie_status(account_id, False)
                    return None
                else:
                    # 其他错误，不锁定cookie
                    return None
            
            # 检查数据是否完整
            if 'data' not in result or 'generalRatio' not in result['data'] or not result['data']['generalRatio']:
                return None
            
            # 如果请求成功，标记cookie为有效
            cookie_rotator.report_cookie_status(account_id, True)
            
            return result
            
        except Exception as e:
            # 如果是超时或网络错误，不锁定cookie
            if account_id and not ('timeout' in str(e).lower() or 'connection' in str(e).lower() or 'read timed out' in str(e).lower()):
                cookie_rotator.report_cookie_status(account_id, False)
            return None
    
    @retry(max_retries=2)
    def get_trend_index(self, keyword, area=0, start_date=None, end_date=None):
        """
        获取趋势指数数据
        :param keyword: 关键词
        :param area: 地区代码，默认为0（全国）
        :param start_date: 开始日期，格式：'yyyy-MM-dd'，默认为当年1月1日
        :param end_date: 结束日期，格式：'yyyy-MM-dd'，默认为当年最后一天
        :return: 趋势指数数据字典或None（请求失败）
        """
        try:
            # 如果未指定日期，使用当前年份的时间范围
            current_year = datetime.now().year
            if not start_date:
                start_date = f"{current_year}-01-01"
            if not end_date:
                if current_year == 2025:
                    end_date = "2025-06-23"  # 2025年只到6月23日
                else:
                    end_date = f"{current_year}-12-31"
            
            # 获取一个可用的cookie
            account_id, cookie_dict = cookie_rotator.get_cookie()
            if not cookie_dict:
                # 检查是否有可用cookie，如果有则立即使用，不等待
                available_count = cookie_rotator.get_status().get('available', 0)
                if available_count > 0:
                    log.info(f"检测到有 {available_count} 个可用Cookie，立即重新获取")
                    account_id, cookie_dict = cookie_rotator.get_cookie()
                    if cookie_dict:
                        log.info(f"成功获取到可用Cookie: {account_id}")
                    else:
                        log.warning(f"尽管显示有可用Cookie，但获取失败")
                
                # 如果仍然没有获取到cookie，等待短暂时间后重试
                if not cookie_dict:
                    log.info(f"get_trend_index 等待Cookie可用...")
                    # 等待有可用的cookie (最多等待5秒，减少等待时间)
                    if cookie_rotator.wait_for_available_cookie(timeout=5):
                        # 重新尝试获取cookie
                        account_id, cookie_dict = cookie_rotator.get_cookie()
                        if not cookie_dict:
                            log.warning(f"get_trend_index 等待Cookie超时，跳过等待继续尝试")
                            return None
                    else:
                        log.warning(f"get_trend_index 等待Cookie超时，跳过等待继续尝试")
                        return None
            
            # 构建请求URL
            encoded_keyword = keyword.replace(' ', '%20')
            url = f'{self.trend_url}?area={area}&word=[[{{"name":"{encoded_keyword}","wordType":1}}]]&startDate={start_date}&endDate={end_date}'
            
            # 生成Cipher-Text参数
            cipher_url = f'{self.referer}#/trend/{encoded_keyword}?words={encoded_keyword}'
            cipher_text = cipher_text_generator.generate(cipher_url)
            
            if not cipher_text:
                return None
            
            # 构建请求头
            headers = self.base_headers.copy()
            headers['Cipher-Text'] = cipher_text
            
            # 频率控制
            rate_limiter.wait()
            
            # 发送请求
            response = requests.get(
                url=url,
                headers=headers,
                cookies=cookie_dict,
                timeout=10
            )
            
            # 检查响应状态
            if response.status_code != 200:
                # 超时或网络错误不锁定Cookie
                if 'timeout' in str(response).lower() or 'connection' in str(response).lower():
                    return None
                else:
                    cookie_rotator.report_cookie_status(account_id, False)
                    return None
            
            # 解析响应内容
            result = response.json()
            
            # 检查API返回的状态码
            if result.get('status') != 0:
                error_msg = result.get('message', '未知错误')
                
                # 如果是"not login"错误，将cookie标记为永久封禁
                if error_msg == "not login":
                    cookie_rotator.report_cookie_status(account_id, False, permanent=True)
                    
                    # 检查是否有可用cookie，如果有则立即使用，不等待
                    available_count = cookie_rotator.get_status().get('available', 0)
                    if available_count > 0:
                        log.info(f"检测到有 {available_count} 个可用Cookie，立即重新获取")
                        return self.get_trend_index(keyword, area, start_date, end_date)
                    
                    # 等待看是否有其他可用Cookie
                    if cookie_rotator.wait_for_available_cookie(timeout=5):
                        # 递归调用自身重试
                        return self.get_trend_index(keyword, area, start_date, end_date)
                    return None
                # 如果是请求频率限制错误（状态码10001），临时锁定cookie
                elif result.get('status') == 10001:
                    cookie_rotator.report_cookie_status(account_id, False)
                    return None
                else:
                    # 其他错误，不锁定cookie
                    return None
            
            # 检查数据是否完整
            if 'data' not in result or 'index' not in result['data'] or not result['data']['index']:
                return None
            
            # 如果请求成功，标记cookie为有效
            cookie_rotator.report_cookie_status(account_id, True)
            
            return result
            
        except Exception as e:
            # 如果是超时或网络错误，不锁定cookie
            if account_id and not ('timeout' in str(e).lower() or 'connection' in str(e).lower() or 'read timed out' in str(e).lower()):
                cookie_rotator.report_cookie_status(account_id, False)
            return None


# 创建百度指数API单例
baidu_index_api = BaiduIndexAPI() 