import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from src.engine.spider.word_graph_crawler import WordGraphCrawler
from src.services.processor_service import data_processor

class TestWordGraphCrawler(unittest.TestCase):
    def setUp(self):
        self.crawler = WordGraphCrawler()
        self.crawler.cookie_rotator = MagicMock()
        self.crawler._update_task_db_status = MagicMock()
        self.crawler._get_cookie_dict = MagicMock(return_value=('account_1', {'cookie': 'value'}))
        self.crawler._generate_task_id = MagicMock(return_value='test_task_id')
        self.crawler._load_global_checkpoint = MagicMock(return_value=None)
        self.crawler._finalize_crawl = MagicMock()
        self.crawler._flush_buffer = MagicMock()

    @patch('src.engine.spider.word_graph_crawler.WordGraphCrawler.get_word_graph')
    def test_process_task_success(self, mock_get_graph):
        mock_response = {'status': 0, 'data': {}}
        mock_get_graph.return_value = mock_response
        
        mock_df = pd.DataFrame([{'word': 'test', 'related': 'foo'}])
        
        with patch.object(data_processor, 'process_word_graph_data', return_value=mock_df) as mock_process:
            task = {'keyword': 'test', 'date': '20230101'}
            result = self.crawler._process_task(task)
            
            mock_get_graph.assert_called_with('test', '20230101')
            mock_process.assert_called_with(mock_response, 'test', '20230101')
            self.assertFalse(result.empty)

    def test_prepare_tasks(self):
        keywords = ['A', 'B']
        datelists = ['20230101', '20230102']
        tasks = self.crawler._prepare_tasks(keywords, datelists)
        
        self.assertEqual(len(tasks), 4)
        expected = [
            {'keyword': 'A', 'date': '20230101'},
            {'keyword': 'A', 'date': '20230102'},
            {'keyword': 'B', 'date': '20230101'},
            {'keyword': 'B', 'date': '20230102'},
        ]
        self.assertEqual(tasks, expected)

    @patch('requests.get')
    def test_get_word_graph_api(self, mock_requests_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 0, 'data': {}}
        mock_requests_get.return_value = mock_response
        
        with patch('src.utils.rate_limiter.rate_limiter.wait'):
            result = self.crawler.get_word_graph('test', '20230101')
            self.assertIsNotNone(result)
            self.assertEqual(result['status'], 0)
