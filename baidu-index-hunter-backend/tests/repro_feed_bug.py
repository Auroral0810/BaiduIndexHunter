
import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys

# Ensure src is in python path
sys.path.append(os.getcwd())

from src.engine.spider.feed_index_crawler import FeedIndexCrawler

class TestFeedCrawlerRepro(unittest.TestCase):
    def setUp(self):
        # Patching dependencies that might fail in environment without real Baidu access
        self.crawler = FeedIndexCrawler()
        
    @patch('src.engine.spider.feed_index_crawler.cipher_text_generator')
    @patch('src.engine.spider.feed_index_crawler.requests.get')
    @patch('src.services.storage_service.StorageService.append_to_csv')
    @patch('src.data.repositories.mysql_manager.MySQLManager.execute_query')
    def test_repro_feed_bug(self, mock_db, mock_storage, mock_get, mock_cipher):
        """Reproduce the feed crawler bug using provided parameters"""
        
        # Setup mocks
        mock_cipher.get_cipher_text.return_value = "test_cipher"
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": 0,
            "data": {
                "index": [{
                    "key": "哈尔滨华德学院",
                    "type": "feed",
                    "startDate": "2026-01-08",
                    "endDate": "2026-02-06",
                    "data": "encrypted_content",
                    "generalRatio": {"avg": 100, "yoy": 10, "qoq": 5}
                }],
                "uniqid": "test_uniqid"
            }
        }
        mock_get.return_value = mock_response
        
        # Mock processor to return dummy data
        with patch('src.services.processor_service.BaiduIndexDataProcessor.process_multi_feed_index_data') as mock_proc:
            mock_proc.return_value = ([{'test': 'data'}], [{'stats': 'data'}])
            
            # Prepare parameters
            params = {
                "keywords": ["哈尔滨华德学院"],
                "cities": {
                    "0": {"name": "全国", "code": "0"},
                    "81": {"name": "淄博市", "code": "81"},
                    "903": {"name": "江西", "code": "903"}
                },
                "resume": False,
                "kind": "all",
                "days": 30
            }
            
            # Execute crawl
            try:
                success = self.crawler.crawl(**params)
                print(f"Crawl success: {success}")
                print(f"Generated Task ID: {self.crawler.task_id}")
                
                # Verify Task ID format (YYYYMMDDHHMMSS_random8)
                import re
                task_id_pattern = r'^\d{14}_[a-f0-9]{8}$'
                self.assertTrue(re.match(task_id_pattern, self.crawler.task_id), 
                                f"Task ID format mismatch: {self.crawler.task_id}")
                print("Task ID format verification passed.")
                
            except Exception as e:
                import traceback
                print(f"Crawl failed with error: {e}")
                print(traceback.format_exc())
                self.fail(f"Crawl raised exception: {e}")

if __name__ == '__main__':
    unittest.main()
