
import unittest
import sys
import os
from unittest.mock import MagicMock, patch
import pandas as pd
import tempfile
import shutil
import glob

# Ensure src is in python path
sys.path.append(os.getcwd())

from src.engine.spider.search_index_crawler import SearchIndexCrawler

class TestSearchIndexCrawlerInterface(unittest.TestCase):
    
    def setUp(self):
        # Mock external dependencies
        self.mock_config_patcher = patch('src.services.config_service.config_manager.get')
        self.mock_config = self.mock_config_patcher.start()
        self.mock_config.return_value = 5  # Mock max_workers

        self.crawler = SearchIndexCrawler()
        
        # Mock methods to allow crawl flow to proceed
        self.crawler._generate_task_id = MagicMock(return_value='test_task_id_123')
        self.crawler._load_keywords_from_file = MagicMock(return_value=['手机'])
        self.crawler._load_cities_from_file = MagicMock(return_value={0: '全国'})
        
        # Mock storage related
        self.os_makedirs_patcher = patch('os.makedirs')
        self.mock_makedirs = self.os_makedirs_patcher.start()
        
        # Mock logging
        self.log_patcher = patch('src.core.logger.log')
        self.mock_log = self.log_patcher.start()
        
        # Mock base crawler methods
        self.crawler._update_task_db_status = MagicMock()
        self.crawler._save_global_checkpoint = MagicMock()
        self.crawler._update_spider_statistics = MagicMock()

    def tearDown(self):
        self.mock_config_patcher.stop()
        self.os_makedirs_patcher.stop()
        self.log_patcher.stop()

    def test_crawl_output_format(self):
        """Test the crawl method execution and verify CSV output format and content."""
        
        keywords = ["手机"]
        cities = {"0": {"name": "全国", "code": "0"}}
        resume = False
        kind = "all"
        days = 30
        
        # 1. Mock _get_search_index response
        mock_response_data = {
            "status": 0,
            "data": {
                "generalRatio": [{
                    "all": {"avg": 100, "yoy": 10, "qoq": 10},
                    "wise": {"avg": 50, "yoy": 5, "qoq": 5},
                    "pc": {"avg": 50, "yoy": 5, "qoq": 5}
                }]
            }
        }
        self.crawler._get_search_index = MagicMock(return_value=(mock_response_data, {}))
        
        # 2. Mock _decrypt to return valid comma-separated string
        # Assuming 30 days, we need ~31 values (start to end inclusive)
        dummy_vals = ",".join(["100"] * 31)
        self.crawler._decrypt = MagicMock(return_value=dummy_vals)
        
        # 3. Setup temporary output directory
        self.test_dir = tempfile.mkdtemp()
        
        # We need to make sure os.makedirs uses the real one for our test dir, but mocked generally?
        # Actually providing a real temp dir is better.
        # But we mocked os.makedirs in setUp. We should unmock it or side_effect it.
        self.os_makedirs_patcher.stop() 
        
        # Patch OUTPUT_DIR
        with patch('src.engine.spider.search_index_crawler.OUTPUT_DIR', self.test_dir):
            try:
                self.crawler.crawl(
                    keywords=keywords,
                    cities=cities,
                    resume=resume,
                    days=days,
                    kind=kind
                )
            except Exception as e:
                self.fail(f"crawl() raised exception: {e}")
        
        # 4. Verify CSV Output
        print(f"Completed Tasks: {self.crawler.completed_tasks}")
        print(f"Failed Tasks: {self.crawler.failed_tasks}")
        
        expected_dir = os.path.join(self.test_dir, 'search_index', 'test_task_id_123')
        if not os.path.exists(expected_dir):
             # Try to list test_dir content recursively to see where it went
            print(f"Expected dir {expected_dir} not found. Listings:")
            for root, dirs, files in os.walk(self.test_dir):
                print(f"{root}: {files}")
        
        csv_pattern = os.path.join(expected_dir, '*_data.csv')
        csv_files = glob.glob(csv_pattern)
        
        if not csv_files:
            # Print mock log calls to see errors
            print("Log calls:")
            for call in self.mock_log.error.call_args_list:
                print(f"ERROR: {call}")
            for call in self.mock_log.warning.call_args_list:
                print(f"WARN: {call}")
                
            self.fail(f"No CSV file generated in {expected_dir}. Files found: {os.listdir(self.test_dir) if os.path.exists(self.test_dir) else 'Dir not found'}")
            
        csv_path = csv_files[0]
        df = pd.read_csv(csv_path)
        
        print(f"\nCSV File: {csv_path}")
        print("Generated CSV Content (First 5 rows):")
        print(df.head())
        print(f"Columns: {df.columns.tolist()}")
        
        # Verify columns
        expected_columns = ['关键词', '城市代码', '城市', '日期', '数据类型', '数据间隔(天)', '所属年份', 'PC+移动指数', '移动指数', 'PC指数', '爬取时间']
        for col in expected_columns:
            self.assertTrue(col in df.columns, f"Column '{col}' missing in CSV. Found: {df.columns.tolist()}")
            
        # Verify no index column (Unnamed: 0 or similar)
        # If '关键词' is the first column, we are good.
        self.assertEqual(df.columns[0], '关键词', f"First column should be '关键词', but got '{df.columns[0]}'")
        
        # Verify data
        self.assertEqual(df.iloc[0]['关键词'], '手机')
        self.assertEqual(str(df.iloc[0]['PC+移动指数']), '100')
        
        # Cleanup
        shutil.rmtree(self.test_dir)

if __name__ == '__main__':
    unittest.main()
