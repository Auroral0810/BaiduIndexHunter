"""
Cipher-Text生成模块，用于生成百度指数API请求所需的加密参数，正确
"""
import os
import execjs
from pathlib import Path
from utils.logger import log
from core.config import CIPHER_TEXT_JS_PATH
from fake_useragent import UserAgent

ua = UserAgent()
useragent=ua.random#随机生成useragent
class CipherTextGenerator:
    """Cipher-Text生成器，调用JS脚本生成加密参数"""
    
    def __init__(self):
        self.js_path = CIPHER_TEXT_JS_PATH
        self.js_context = None
        self._init_js_context()
    
    def _init_js_context(self):
        """初始化JS执行环境"""
        try:
            if not os.path.exists(self.js_path):
                log.error(f"Cipher-Text.js文件不存在: {self.js_path}")
                return False
            
            with open(self.js_path, 'r', encoding='utf-8') as f:
                js_code = f.read()
            
            self.js_context = execjs.compile(js_code)
            log.info("Cipher-Text.js加载成功")
            return True
        except Exception as e:
            log.error(f"初始化JS执行环境失败: {e}")
            self.js_context = None
            return False
    
    def generate(self, url):
        """
        生成Cipher-Text参数
        :param url: 原始URL，例如 'https://index.baidu.com/v2/main/index.html#/trend/关键词?words=关键词'
        :return: 生成的Cipher-Text值或None（如果生成失败）
        """
        if not self.js_context:
            if not self._init_js_context():
                return None
        
        try:
            cipher_text = self.js_context.call('ascToken', url, useragent)
            log.debug(f"生成Cipher-Text成功: {cipher_text[:20]}...")
            return cipher_text
        except Exception as e:
            log.error(f"生成Cipher-Text失败: {e}")
            return None


# 创建Cipher-Text生成器单例
cipher_text_generator = CipherTextGenerator() 
