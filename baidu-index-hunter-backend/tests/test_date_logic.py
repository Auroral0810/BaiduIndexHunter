
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import sys
import os

# Ensure src is in python path
sys.path.append(os.getcwd())

from src.engine.spider.search_index_crawler import SearchIndexCrawler

class TestDateLogic(unittest.TestCase):
    
    def setUp(self):
        self.crawler = SearchIndexCrawler()
        self.crawler._load_keywords_from_file = MagicMock(return_value=['test'])
        self.crawler._load_cities_from_file = MagicMock(return_value={0: '全国'})
        self.crawler._process_task = MagicMock()
        self.crawler._update_task_db_status = MagicMock()
        self.crawler._flush_buffer = MagicMock()

    @patch('src.engine.spider.search_index_crawler.log')
    @patch('src.engine.spider.search_index_crawler.ThreadPoolExecutor')
    @patch('src.engine.spider.search_index_crawler.as_completed')
    def test_days_calculation(self, mock_as_completed, mock_executor, mock_log):
        # mock_as_completed should return an iterator of the futures
        mock_future = MagicMock()
        mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future
        mock_as_completed.return_value = [mock_future]
        
        days = 30
        try:
            # We must mock output_path creation to avoid permissions issues or real file creation
            self.crawler.output_path = "/tmp/test"
            with patch('os.makedirs'):
                self.crawler.crawl(days=days, keywords=['test'], cities={0: 'test'})
        except Exception as e:
            # We don't care if it fails later, but we should not fail on CrawlerInterrupted
            print(f"Crawl internal error (expected in mock): {e}")
        
        # Check logs for "最终使用的 date_ranges"
        # The log message is: "最终使用的 date_ranges 长度: 1"
        # But we want the value. The log before that is:
        # log.info(f"爬虫接收到的 date_ranges 参数: {date_ranges}...") 
        # Wait, that logs the *input* argument.
        
        # We need to find where it logs the calculated range.
        # It doesn't seem to log the *calculated* range explicitly except maybe in the loop or "理论总任务数".
        # Or we can check what `all_tasks` was generated with if we could inspect `_process_task` calls.
        # But logic is inside crawl.
        
        # Let's rely on checking the input to ThreadPoolExecutor or explicit calculation if we can.
        # The crawl method calls `date_ranges = [...]`.
        
        # Better approach:
        # Since I modified the code to calculate `start_date` and `end_date`, I can just
        # run a small script that imports the class and inspects the logic if I extract it?
        # No, I can't extract it easily without changing code structure.
        
        # Let's check `mock_log.info` calls.
        # It logs: log.info(f"总任务数: ... (关键词: ..., 城市: ..., 日期范围: {len(date_ranges)})")
        
        # Actually I can inspect the `all_tasks` passed to `_process_task`?
        # `executor.submit(self._process_task, task)`
        # `task` is `(keywords, city_code, city_name, start_date, end_date)` (for batch)
        # or `(keyword, city_code, city_name, start_date, end_date)` (for single)
        
        # We Mocked ThreadPoolExecutor. adapter pattern `with ThreadPoolExecutor(...) as executor`
        # executor.submit is called.
        
        instance = mock_executor.return_value.__enter__.return_value
        # verify calls to instance.submit
        
        self.assertTrue(instance.submit.called)
        call_args = instance.submit.call_args[0]
        # args[0] is func, args[1] is task
        task = call_args[1]
        
        # task structure: (keywords_list/str, city_code, city_name, start, end)
        start_date = task[3]
        end_date = task[4]
        
        print(f"Calculated Start: {start_date}, End: {end_date}")
        
        today = datetime.now()
        expected_end = (today - timedelta(days=2)).strftime('%Y-%m-%d')
        expected_start = (today - timedelta(days=days+1)).strftime('%Y-%m-%d')
        
        self.assertEqual(end_date, expected_end)
        self.assertEqual(start_date, expected_start)

if __name__ == '__main__':
    unittest.main()
