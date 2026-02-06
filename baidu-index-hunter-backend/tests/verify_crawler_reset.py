
import os
import sys
from unittest.mock import MagicMock, patch

# Mock some dependencies to avoid actual API calls
sys.modules['src.services.storage_service'] = MagicMock()
sys.modules['src.services.cookie_rotator'] = MagicMock()
sys.modules['src.services.processor_service'] = MagicMock()
sys.modules['src.utils.rate_limiter'] = MagicMock()

from src.engine.spider.word_graph_crawler import WordGraphCrawler
from src.core.logger import log

def test_singleton_reset():
    crawler = WordGraphCrawler()
    
    # Simulate a first run
    print("--- First Run (1 task) ---")
    with patch.object(crawler, 'get_word_graph', return_value={'status': 0, 'data': {'wordlist': []}, 'period': '20250209|20260201'}):
        with patch.object(crawler, '_flush_buffer'):
            crawler.crawl(keywords=['test1'], datelists=['20250209'])
    
    print(f"Completed after run 1: {crawler.completed_tasks}/{crawler.total_tasks}")
    
    # Simulate a second run
    print("\n--- Second Run (1 task) ---")
    with patch.object(crawler, 'get_word_graph', return_value={'status': 0, 'data': {'wordlist': []}, 'period': '20250209|20260201'}):
        with patch.object(crawler, '_flush_buffer'):
            crawler.crawl(keywords=['test2'], datelists=['20250216'])
            
    print(f"Completed after run 2: {crawler.completed_tasks}/{crawler.total_tasks}")
    
    if crawler.completed_tasks == 1:
        print("\nSUCCESS: State correctly reset between runs.")
    else:
        print(f"\nFAILURE: State NOT reset correctly. completed_tasks is {crawler.completed_tasks}, expected 1.")

if __name__ == "__main__":
    try:
        test_singleton_reset()
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
