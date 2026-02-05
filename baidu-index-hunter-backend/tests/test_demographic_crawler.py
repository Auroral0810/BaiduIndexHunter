import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from src.engine.spider.demographic_attributes_crawler import DemographicAttributesCrawler
from src.services.processor_service import data_processor

class TestDemographicAttributesCrawler(unittest.TestCase):
    def setUp(self):
        self.crawler = DemographicAttributesCrawler()
        self.crawler.cookie_rotator = MagicMock()
        self.crawler._update_task_db_status = MagicMock()
        self.crawler._get_cookie_dict = MagicMock(return_value=('account_1', {'cookie': 'value'}))
        self.crawler._generate_task_id = MagicMock(return_value='test_task_id')
        self.crawler._load_global_checkpoint = MagicMock(return_value=None)
        self.crawler._finalize_crawl = MagicMock()
        self.crawler._flush_buffer = MagicMock()

    @patch('src.engine.spider.demographic_attributes_crawler.DemographicAttributesCrawler.get_demographic_attributes')
    def test_process_task_success(self, mock_get_demo):
        mock_response = {'status': 0, 'data': {}}
        mock_get_demo.return_value = mock_response
        
        mock_df = pd.DataFrame([{'word': 'test', 'age': '20-29'}])
        
        with patch.object(data_processor, 'process_demographic_data', return_value=mock_df) as mock_process:
            result = self.crawler._process_task(['test'])
            
            mock_get_demo.assert_called_with(['test'])
            mock_process.assert_called_with(mock_response)
            self.assertFalse(result.empty)

    @patch('src.engine.spider.demographic_attributes_crawler.DemographicAttributesCrawler.get_demographic_attributes')
    def test_process_task_failure(self, mock_get_demo):
        mock_get_demo.return_value = None
        
        with self.assertRaises(Exception):
            self.crawler._process_task(['test'])

    @patch('requests.get')
    def test_get_demographic_attributes_api(self, mock_requests_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 0, 'data': {}}
        mock_requests_get.return_value = mock_response
        
        with patch('src.utils.rate_limiter.rate_limiter.wait'):
            result = self.crawler.get_demographic_attributes(['test'])
            self.assertIsNotNone(result)
            self.assertEqual(result['status'], 0)

    def test_prepare_tasks(self):
        tasks = self.crawler._prepare_tasks(['a', 'b', 'c'], batch_size=2)
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0], ['a', 'b'])
        self.assertEqual(tasks[1], ['c'])
