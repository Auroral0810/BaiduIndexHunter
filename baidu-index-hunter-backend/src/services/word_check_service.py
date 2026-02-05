"""
关键词检查服务 - 业务逻辑与缓存层
"""
import concurrent.futures
from typing import List, Dict, Any
from src.core.logger import log
from src.core.redis import redis_client
from src.engine.spider.word_check_spider import word_check_spider

class WordCheckService:
    """关键词检查服务：负责缓存管理与并发调度"""
    
    REDIS_KEY_PREFIX = "word_check:"
    
    def _get_cache_key(self, word: str) -> str:
        return f"{self.REDIS_KEY_PREFIX}{word}"

    def check_single_word(self, word: str) -> Dict[str, Any]:
        """
        检查单个关键词，优先查查缓存
        """
        cache_key = self._get_cache_key(word)
        
        # 1. 尝试从 Redis 获取 (永久存储，1表示存在，0表示不存在)
        cached_val = redis_client.get(cache_key)
        if cached_val is not None:
            log.info(f"关键词 '{word}' 命中缓存: {cached_val}")
            return {
                'word': word,
                'exists': cached_val == "1",
                'from_cache': True
            }
        
        # 2. 缓存未命中，调用爬虫
        exists, result = word_check_spider.check_word(word)
        
        # 3. 如果请求成功（非网络/账号错误），同步到 Redis
        if isinstance(result, dict): # 表示 API 返回了正常结构
            redis_client.set(cache_key, "1" if exists else "0")
            log.info(f"关键词 '{word}' 已更新至缓存: {exists}")
            return {
                'word': word,
                'exists': exists,
                'from_cache': False
            }
        else:
            # 记录错误但不缓存
            return {
                'word': word,
                'exists': False,
                'error': str(result)
            }

    def check_words(self, words: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        并行批量检查关键词
        """
        results = {}
        # 去重
        unique_words = list(set(words))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(unique_words), 10)) as executor:
            future_to_word = {executor.submit(self.check_single_word, word): word for word in unique_words}
            for future in concurrent.futures.as_completed(future_to_word):
                word = future_to_word[future]
                try:
                    results[word] = future.result()
                except Exception as e:
                    results[word] = {'exists': False, 'error': str(e)}
        
        return results

# 全局单例
word_check_service = WordCheckService()
