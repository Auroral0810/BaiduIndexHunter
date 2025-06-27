"""
Cookie验证模块，用于检查cookie的有效性（未使用）
"""
import requests
import time
import json
from utils.logger import log
from config.settings import BAIDU_INDEX_API


class CookieValidator:
    """Cookie验证器，检测百度指数Cookie是否有效"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': BAIDU_INDEX_API['user_agent'],
            'Referer': 'https://index.baidu.com/v2/main/index.html',
            'Connection': 'keep-alive',
        }
        self.test_keyword = "百度"  # 用于测试的关键词
        self.search_url = BAIDU_INDEX_API['search_url']
    
    def validate_cookie(self, cookie_value):
        """
        验证cookie是否有效
        :param cookie_value: cookie字符串
        :return: (bool, str) - (是否有效, 失效原因)
        """
        try:
            # 解析cookie字符串或使用整个字符串
            if isinstance(cookie_value, dict):
                cookie_dict = cookie_value
            else:
                cookie_dict = self._parse_cookie_string(cookie_value)
            
            # 添加Cookie到请求头
            headers = self.headers.copy()
            
            # 构造请求参数
            params = {
                'word': json.dumps([[{'name': self.test_keyword, 'wordType': 1}]]),
                'area': '0',
                'days': '30',
            }
            
            # 发送请求
            response = requests.get(
                self.search_url,
                params=params,
                headers=headers,
                cookies=cookie_dict,
                timeout=30
            )
            
            # 解析响应
            data = response.json()
            
            # 检查状态码和响应内容
            if response.status_code == 200:
                if data.get('status') == 0 and 'data' in data:
                    log.debug(f"Cookie验证成功: {self.test_keyword}")
                    return True, ""
                else:
                    error_msg = data.get('message', '未知错误')
                    log.warning(f"Cookie验证失败: {error_msg}")
                    return False, error_msg
            else:
                log.warning(f"Cookie验证请求失败, 状态码: {response.status_code}")
                return False, f"HTTP错误: {response.status_code}"
            
        except requests.RequestException as e:
            log.error(f"验证Cookie时发生网络错误: {e}")
            return False, f"网络错误: {str(e)}"
        except Exception as e:
            log.error(f"验证Cookie时发生未知错误: {e}")
            return False, f"未知错误: {str(e)}"
    
    def _parse_cookie_string(self, cookie_string):
        """
        将cookie字符串解析为字典
        :param cookie_string: cookie字符串
        :return: cookie字典
        """
        cookie_dict = {}
        if not cookie_string:
            return cookie_dict
            
        # 处理可能的JSON格式
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


# 创建Cookie验证器单例
cookie_validator = CookieValidator() 