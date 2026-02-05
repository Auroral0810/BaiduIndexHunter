import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from src.engine.spider.region_distribution_crawler import RegionDistributionCrawler
from src.services.processor_service import data_processor

class TestRegionDistributionCrawler(unittest.TestCase):
    def setUp(self):
        self.crawler = RegionDistributionCrawler()
        self.crawler.cookie_rotator = MagicMock()
        self.crawler._update_task_db_status = MagicMock()
        self.crawler._get_cookie_dict = MagicMock(return_value=('account_1', {'cookie': 'value'}))
        self.crawler._generate_task_id = MagicMock(return_value='test_task_id')
        self.crawler._load_global_checkpoint = MagicMock(return_value=None)
        self.crawler._finalize_crawl = MagicMock()
        self.crawler._flush_buffer = MagicMock()

    @patch('src.engine.spider.region_distribution_crawler.RegionDistributionCrawler.get_region_distribution')
    def test_process_task_success(self, mock_get_region):
        mock_response = {'status': 0, 'data': {}}
        mock_get_region.return_value = mock_response
        
        mock_df = pd.DataFrame([{'word': 'test', 'province': 'Shandong'}])
        
        with patch.object(data_processor, 'process_region_distribution_data', return_value=mock_df) as mock_process:
            task = {'keyword': 'test', 'region': 0, 'start_date': '2023-01-01', 'end_date': '2023-01-30'}
            result = self.crawler._process_task(task)
            
            mock_get_region.assert_called_with(keywords=['test'], region=0, start_date='2023-01-01', end_date='2023-01-30')
            mock_process.assert_called_with(mock_response, 0, 'test', '2023-01-01', '2023-01-30')
            self.assertFalse(result.empty)

    def test_prepare_tasks(self):
        keywords = ['A']
        regions = [0, 1]
        date_ranges = [('2023-01-01', '2023-01-30')]
        
        tasks = self.crawler._prepare_tasks(keywords, regions, date_ranges)
        
        self.assertEqual(len(tasks), 2)
        expected = [
            {'keyword': 'A', 'region': 0, 'start_date': '2023-01-01', 'end_date': '2023-01-30'},
            {'keyword': 'A', 'region': 1, 'start_date': '2023-01-01', 'end_date': '2023-01-30'},
        ]
        self.assertEqual(tasks, expected)

    @patch('requests.get')
    def test_get_region_distribution_api(self, mock_requests_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 0, 'data': {}}
        mock_requests_get.return_value = mock_response
        
        with patch('src.utils.rate_limiter.rate_limiter.wait'):
            result = self.crawler.get_region_distribution(['test'], 0, start_date='2023-01-01', end_date='2023-01-30')
            self.assertIsNotNone(result)
            self.assertEqual(result['status'], 0)
