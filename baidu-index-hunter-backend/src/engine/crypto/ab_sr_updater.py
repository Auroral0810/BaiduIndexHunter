"""
百度指数ab_sr cookie更新模块
"""
import requests
import json
import execjs
import os
import time
from pathlib import Path
from fake_useragent import UserAgent
from src.core.logger import log


class AbSrUpdater:
    """百度指数ab_sr cookie更新器"""
    
    def __init__(self, js_path=None):
        """
        初始化ab_sr更新器
        :param js_path: ab_sr.js文件路径，如果为None则使用默认路径
        """
        self.ua = UserAgent()
        self.url = "https://miao.baidu.com/abdr"
        self.params = {
            "_o": "https://index.baidu.com"
        }
        
        # 如果未指定js_path，则使用默认路径
        if js_path is None:
            # 获取当前文件所在目录
            current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
            self.js_path = current_dir / "ab_sr.js"
        else:
            self.js_path = Path(js_path)
    
    def _get_headers(self):
        """
        生成请求头
        :return: 请求头字典
        """
        # 固定 User-Agent 以匹配 Client Hints
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        return {
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/plain;charset=UTF-8",
            "Origin": "https://index.baidu.com",
            "Pragma": "no-cache",
            "Referer": "https://index.baidu.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": user_agent,
            "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"macOS\""
        }
    
    def _load_js_code(self):
        """
        加载JS代码
        :return: JS代码字符串
        """
        try:
            with open(self.js_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(self.js_path, 'r', encoding='gbk', errors='ignore') as f:
                    return f.read()
            except Exception as e:
                log.error(f"加载ab_sr.js文件失败: {e}")
                return None

    def update_ab_sr(self, max_retries=3):
        """
        更新ab_sr cookie
        :param max_retries: 最大重试次数
        :return: 更新后的ab_sr值，如果失败则返回None
        """
        
        for attempt in range(max_retries):
            try:
                # 加载JS代码
                js_code = self._load_js_code()
                if not js_code:
                    return None
                
                # 编译JS代码
                ctx = execjs.compile(js_code)
                data_js = ctx.call('get_data')
                
                data_obj = json.loads(data_js)
                
                # 使用从JS获取的数据构建请求体
                data = {
                    "data": data_obj["data"],
                    "key_id": data_obj["key_id"],
                    "enc": data_obj["enc"]
                }
                
                # 将数据转换为JSON字符串，不包含空格
                data_json = json.dumps(data, separators=(',', ':'))
                
                # 发送请求
                headers = self._get_headers()
                response = requests.post(self.url, headers=headers, params=self.params, data=data_json, timeout=10)
                
                # 获取ab_sr cookie
                ab_sr = response.cookies.get('ab_sr')
                
                if ab_sr:
                    # log.info(f"成功更新ab_sr: {ab_sr}")
                    return ab_sr
                else:
                    log.warning(f"更新ab_sr失败 (尝试 {attempt+1}/{max_retries}): Status: {response.status_code}, Body: {response.text[:200]}")
                    
                    # 如果是400错误，可能是因为请求频繁或者参数问题，稍微等待一下
                    if attempt < max_retries - 1:
                        time.sleep(1.5 * (attempt + 1))
                        continue
                        
                    return None
                    
            except Exception as e:
                log.error(f"更新ab_sr时发生错误 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    return None
        return None