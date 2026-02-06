
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
            "status": 1,
            "data": "",
            "message": "no data"
        }
        mock_get.return_value = mock_response
        
        # No longer mocking processor, to test real logic with status 1
        if True:
            
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
                # Patch _get_feed_index to capture arguments
                with patch.object(self.crawler, '_get_feed_index') as mock_get_feed:
                    mock_get_feed.return_value = (mock_response.json(), {})
                    
                    success = self.crawler.crawl(**params)
                    
                    # Get the dates used in the call
                    args, kwargs = mock_get_feed.call_args
                    # _get_feed_index signature: (area, keywords, start_date=None, end_date=None, days=None)
                    captured_start = args[2]
                    captured_end = args[3]
                    
                    print(f"Captured start: {captured_start}, end: {captured_end}")
                    
                    from datetime import datetime, timedelta
                    expected_end = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
                    expected_start = (datetime.now() - timedelta(days=31)).strftime('%Y-%m-%d')
                    
                    self.assertEqual(captured_end, expected_end, f"End date mismatch: {captured_end} != {expected_end}")
                    self.assertEqual(captured_start, expected_start, f"Start date mismatch: {captured_start} != {expected_start}")
                    print("Date window verification passed (30 days total).")

                print(f"Generated Task ID: {self.crawler.task_id}")
                
                # Check CSV output
                csv_dir = os.path.join("output", "feed_index", self.crawler.task_id)
                csv_path = os.path.join(csv_dir, f"feed_index_{self.crawler.task_id}_data.csv")
                
                if os.path.exists(csv_path):
                    import pandas as pd
                    df = pd.read_csv(csv_path)
                    print(f"CSV Row Count: {len(df)}")
                    # Expected: 3 cities * 30 days = 90 rows
                    self.assertEqual(len(df), 90, f"Expected 90 rows (3 cities * 30 days), got {len(df)}")
                    self.assertTrue((df['资讯指数'] == 0).all(), "Expect all values to be 0 for status 1")
                    print("CSV content verification passed.")
                else:
                    self.fail(f"CSV file not found at {csv_path}")
                
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
