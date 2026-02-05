import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from src.engine.spider.interest_profile_crawler import InterestProfileCrawler
from src.services.processor_service import data_processor

class TestInterestProfileCrawler(unittest.TestCase):
    def setUp(self):
        # Patching BaseCrawler methods and external dependencies to prevent actual execution
        self.crawler = InterestProfileCrawler()
        self.crawler.cookie_rotator = MagicMock()
        self.crawler._update_task_db_status = MagicMock()
        self.crawler._get_cookie_dict = MagicMock(return_value=('account_1', {'cookie': 'value'}))
        self.crawler._generate_task_id = MagicMock(return_value='test_task_id')
        self.crawler._load_global_checkpoint = MagicMock(return_value=None)
        self.crawler._finalize_crawl = MagicMock()
        self.crawler._flush_buffer = MagicMock()
        
    @patch('src.engine.spider.interest_profile_crawler.InterestProfileCrawler.get_interest_profiles')
    def test_process_task_success(self, mock_get_interest):
        # Mock API response
        mock_response = {'status': 0, 'data': [{'word': 'test', 'interest': []}]}
        mock_get_interest.return_value = mock_response
        
        # Mock processor response
        mock_df = pd.DataFrame([{'word': 'test', 'interest': 'sport'}])
        
        # Patch data_processor method
        with patch.object(data_processor, 'process_interest_profile_data', return_value=mock_df) as mock_process:
            result = self.crawler._process_task(['test'])
            
            mock_get_interest.assert_called_with(['test'])
            mock_process.assert_called_with(mock_response)
            self.assertFalse(result.empty)
            self.assertEqual(result.iloc[0]['word'], 'test')

    @patch('src.engine.spider.interest_profile_crawler.InterestProfileCrawler.get_interest_profiles')
    def test_process_task_failure(self, mock_get_interest):
        mock_get_interest.return_value = None
        
        with self.assertRaises(Exception) as context:
            self.crawler._process_task(['test'])
        
        self.assertTrue("Failed to get interest profiles" in str(context.exception))

    @patch('requests.get')
    def test_get_interest_profiles_api(self, mock_requests_get):
        # Mock successful API call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 0, 'data': {}}
        mock_requests_get.return_value = mock_response
        
        # We need to mock rate_limiter.wait to avoid delay
        with patch('src.utils.rate_limiter.rate_limiter.wait'):
            result = self.crawler.get_interest_profiles(['test'])
            
            self.assertIsNotNone(result)
            self.assertEqual(result['status'], 0)
            self.crawler.cookie_rotator.report_cookie_status.assert_called_with('account_1', True)

    def test_prepare_tasks(self):
        keywords = ['a', 'b', 'c', 'd', 'e', 'f']
        batches = self.crawler._prepare_tasks(keywords, batch_size=2)
        
        self.assertEqual(len(batches), 3)
        self.assertEqual(batches[0], ['a', 'b'])
        self.assertEqual(batches[1], ['c', 'd'])
        self.assertEqual(batches[2], ['e', 'f'])
