"""
关键词检查服务
提供关键词检查的业务逻辑处理
"""
from typing import List, Dict, Any, Optional
from src.core.logger import log
from src.engine.spider.word_check_spider import word_check_spider

class WordCheckService:
    """关键词检查服务类"""
    
    def check_words(self, words: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        批量检查关键词
        Returns:
            Dict[str, Dict]: 关键词检查结果，已清洗格式
        """
        log.info(f"开始检查 {len(words)} 个关键词")
        results = word_check_spider.check_words_batch(words)
        
        # 清洗结果
        clean_results = {}
        for word, result in results.items():
            clean_results[word] = {
                'exists': result.get('exists', False),
            }
            if 'error' in result:
                clean_results[word]['error'] = result['error']
        
        return clean_results

    def check_single_word(self, word: str) -> Dict[str, Any]:
        """
        检查单个关键词
        Returns:
            Dict[str, Any]: 检查结果
        """
        log.info(f"检查关键词: {word}")
        result = word_check_spider.check_word(word)
        
        clean_result = {
            'word': word,
            'exists': result.get('exists', False)
        }
        if 'error' in result:
            clean_result['error'] = result['error']
            
        return clean_result

# 全局实例
word_check_service = WordCheckService()
