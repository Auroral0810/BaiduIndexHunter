import threading
import time
import requests
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.core.logger import log
from src.utils.rate_limiter import rate_limiter
from src.utils.decorators import retry
from src.services.cookie_rotator import cookie_rotator
from src.core.config import BAIDU_INDEX_API


class WordCheckSpider:
    """关键词检查爬虫，用于检查百度指数中关键词是否存在"""
    
    def __init__(self, max_workers=10):
        """
        初始化爬虫
        
        参数:
            max_workers (int): 最大线程数，默认为10
        """
        self.cookie_rotator = cookie_rotator
        self.check_url = "https://index.baidu.com/api/AddWordApi/checkWordsExists"
        self.lock = threading.RLock()
        self.max_workers = max_workers
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Referer": BAIDU_INDEX_API['referer'],
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": BAIDU_INDEX_API['user_agent'],
            "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"macOS\""
        }
        
    @retry(max_retries=3, delay=2)
    def check_word(self, word: str) -> Dict[str, Any]:
        """
        检查单个关键词是否存在
        
        参数:
            word (str): 要检查的关键词
            
        返回:
            Dict[str, Any]: 检查结果，格式为 {"exists": True/False, "response": 原始响应}
        """
        # 使用rate_limiter来限制请求频率
        # rate_limiter.wait()
        
        # 获取有效的Cookie
        with self.lock:
            account_id, cookie_dict = self.cookie_rotator.get_cookie()
        
        if not cookie_dict:
            log.warning("所有Cookie均被锁定，等待30分钟后重试")
            time.sleep(1800)  # 等待30分钟
            return {"exists": False, "error": "无可用Cookie", "response": None}
        
        # 构建请求参数
        params = {"word": word}
        
        try:
            # 发送请求
            response = requests.get(
                self.check_url, 
                headers=self.headers, 
                cookies=cookie_dict, 
                params=params,
                timeout=10
            )
            
            # 检查响应状态
            if response.status_code != 200:
                log.error(f"请求失败: {response.status_code}")
                return {"exists": False, "error": f"请求失败: {response.status_code}", "response": None}
            
            # 解析响应
            data = response.json()
            
            # 检查状态码
            status = data.get('status')
            if status == 0:
                # 状态码为0表示请求成功
                result = data.get('data', {}).get('result', [])
                # 如果result为空列表，说明关键词存在
                exists = len(result) == 0
                return {"exists": exists, "response": data}
            else:
                # 其他状态码表示请求失败
                message = data.get('message', '未知错误')
                log.error(f"检查关键词失败: {message}")
                
                # 检查是否是Cookie失效
                if status == 10000:  # 未登录
                    log.warning(f"Cookie无效或已过期: {account_id}")
                    with self.lock:
                        self.cookie_rotator.report_cookie_status(account_id, False, permanent=True)
                elif status == 10001:  # 请求被锁定
                    log.warning(f"Cookie被临时锁定: {account_id}")
                    with self.lock:
                        self.cookie_rotator.report_cookie_status(account_id, False)
                
                return {"exists": False, "error": message, "response": data}
                
        except Exception as e:
            log.error(f"检查关键词时出错: {str(e)}")
            return {"exists": False, "error": str(e), "response": None}
    
    def check_words_batch(self, words: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        批量检查关键词是否存在
        
        参数:
            words (List[str]): 要检查的关键词列表
            
        返回:
            Dict[str, Dict[str, Any]]: 检查结果，格式为 {关键词: {"exists": True/False, "response": 原始响应}}
        """
        results = {}
        
        # 使用ThreadPoolExecutor实现多线程并发检测
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_word = {executor.submit(self.check_word, word): word for word in words}
            
            # 获取结果
            for future in as_completed(future_to_word):
                word = future_to_word[future]
                try:
                    result = future.result()
                    results[word] = result
                    log.info(f"检查关键词完成: {word}, 结果: {'存在' if result.get('exists') else '不存在'}")
                except Exception as e:
                    log.error(f"处理关键词 {word} 时出错: {str(e)}")
                    results[word] = {"exists": False, "error": str(e), "response": None}
        
        return results
    
    def check_words_batch_with_progress(self, words: List[str], callback=None) -> Dict[str, Dict[str, Any]]:
        """
        批量检查关键词是否存在，并支持进度回调
        
        参数:
            words (List[str]): 要检查的关键词列表
            callback (callable): 进度回调函数，接收参数(完成数, 总数, 当前关键词, 当前结果)
            
        返回:
            Dict[str, Dict[str, Any]]: 检查结果，格式为 {关键词: {"exists": True/False, "response": 原始响应}}
        """
        results = {}
        total = len(words)
        completed = 0
        
        # 使用ThreadPoolExecutor实现多线程并发检测
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_word = {executor.submit(self.check_word, word): word for word in words}
            
            # 获取结果
            for future in as_completed(future_to_word):
                word = future_to_word[future]
                try:
                    result = future.result()
                    results[word] = result
                    completed += 1
                    log.info(f"检查关键词完成 [{completed}/{total}]: {word}, 结果: {'存在' if result.get('exists') else '不存在'}")
                    
                    # 调用回调函数
                    if callback:
                        callback(completed, total, word, result)
                        
                except Exception as e:
                    log.error(f"处理关键词 {word} 时出错: {str(e)}")
                    results[word] = {"exists": False, "error": str(e), "response": None}
                    completed += 1
                    
                    # 调用回调函数
                    if callback:
                        callback(completed, total, word, {"exists": False, "error": str(e)})
        
        return results


# 创建爬虫实例
word_check_spider = WordCheckSpider(max_workers=10)  # 默认使用10个线程 