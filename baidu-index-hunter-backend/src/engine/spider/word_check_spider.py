"""
关键词检查爬虫 - 原子请求层
"""
import requests
from src.core.logger import log
from src.utils.decorators import retry
from src.services.cookie_rotator import cookie_rotator
from src.core.config import BAIDU_INDEX_API

class WordCheckSpider:
    """原子化的关键词检查爬虫"""
    
    def __init__(self):
        self.check_url = "https://index.baidu.com/api/AddWordApi/checkWordsExists"
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": BAIDU_INDEX_API['referer'],
            "User-Agent": BAIDU_INDEX_API['user_agent'],
            "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"macOS\""
        }
        
    @retry(max_retries=3, delay=2)
    def check_word(self, word: str):
        """
        核心原子方法：检查单个关键词是否存在
        返回: (bool, raw_data_or_error_msg)
        """
        account_id, cookie_dict = cookie_rotator.get_cookie()
        if not cookie_dict:
            return False, "无可用Cookie"
        
        try:
            response = requests.get(
                self.check_url, 
                headers=self.headers, 
                cookies=cookie_dict, 
                params={"word": word},
                timeout=10
            )
            
            if response.status_code != 200:
                return False, f"HTTP {response.status_code}"
            
            data = response.json()
            status = data.get('status')
            
            if status == 0:
                # 状态 0 且 result 为空表示关键词存在
                result = data.get('data', {}).get('result', [])
                return len(result) == 0, data
            
            # 异常状态处理
            message = data.get('message', '未知外部错误')
            if status in [10000, 10001]: # 10000:未登录, 10001:请求被锁定
                log.warning(f"Cookie {account_id} 状态异常 ({status}): {message}")
                cookie_rotator.report_cookie_status(account_id, False, permanent=(status == 10000))
            
            return False, message
                
        except Exception as e:
            log.error(f"WordCheckSpider 请求异常: {e}")
            return False, str(e)

# 全局单例
word_check_spider = WordCheckSpider()