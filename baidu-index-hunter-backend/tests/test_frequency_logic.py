
import unittest
from datetime import datetime, timedelta
import sys
import os

# Ensure src is in python path
sys.path.append(os.getcwd())

from src.engine.processors.search_processor import SearchProcessor

class TestFrequencyLogic(unittest.TestCase):
    
    def setUp(self):
        self.processor = SearchProcessor()
    
    def test_daily_detection(self):
        """Test detection of daily data (normal case)"""
        start_date = "2024-01-01"
        end_date = "2024-01-10" # 10 days
        
        # 10 data points
        decrypted_all = ",".join(["100"] * 10)
        decrypted_wise = ",".join(["50"] * 10)
        decrypted_pc = ",".join(["50"] * 10)
        
        data = {"data": {"generalRatio": [{"all": {"avg": 100}}]}}
        
        daily_data, _ = self.processor.process_search_index_daily_data(
            data, {}, "test", 0, "test", start_date, end_date, 
            decrypted_all, decrypted_wise, decrypted_pc
        )
        
        self.assertEqual(len(daily_data), 10)
        self.assertEqual(daily_data[0]['数据类型'], '日度')
        self.assertEqual(daily_data[0]['数据间隔(天)'], 1)
        self.assertEqual(daily_data[0]['日期'], '2024-01-01')
        self.assertEqual(daily_data[1]['日期'], '2024-01-02')

    def test_weekly_detection(self):
        """Test detection of weekly data (long range, few points)"""
        start_date = "2024-01-01"
        # 2 years ~ 730 days. Weekly data ~ 104 points.
        # Let's simulate smaller range but still > 2x ratio
        # 30 days range, but only 4 points (weekly approx)
        end_date = "2024-01-30" # 30 days
        
        # 4 data points (one per week approx)
        decrypted_all = ",".join(["100"] * 4)
        decrypted_wise = ",".join(["50"] * 4)
        decrypted_pc = ",".join(["50"] * 4)
        
        data = {"data": {"generalRatio": [{"all": {"avg": 100}}]}}
        
        daily_data, _ = self.processor.process_search_index_daily_data(
            data, {}, "test", 0, "test", start_date, end_date, 
            decrypted_all, decrypted_wise, decrypted_pc
        )
        
        self.assertEqual(len(daily_data), 30) # Should be padded to 30 days
        self.assertEqual(daily_data[0]['数据类型'], '日度')
        self.assertEqual(daily_data[0]['数据间隔(天)'], 1)
        self.assertEqual(daily_data[0]['日期'], '2024-01-01')
        self.assertEqual(daily_data[1]['日期'], '2024-01-02')

    def test_short_duration_missing_data(self):
        """Test short duration with missing data (should be daily + padded)"""
        start_date = "2024-01-01"
        end_date = "2024-01-30" # 30 days
        
        # 4 data points
        decrypted_all = ",".join(["100"] * 4)
        decrypted_wise = ",".join(["50"] * 4)
        decrypted_pc = ",".join(["50"] * 4)
        
        data = {"data": {"generalRatio": [{"all": {"avg": 100}}]}}
        
        daily_data, _ = self.processor.process_search_index_daily_data(
            data, {}, "test", 0, "test", start_date, end_date, 
            decrypted_all, decrypted_wise, decrypted_pc
        )
        
        # Should be daily (<= 365 days) and padded to 30
        self.assertEqual(len(daily_data), 30)
        self.assertEqual(daily_data[0]['数据类型'], '日度')
        self.assertEqual(daily_data[0]['数据间隔(天)'], 1)
        self.assertEqual(daily_data[0]['日期'], '2024-01-01')
        self.assertEqual(daily_data[4]['PC+移动指数'], '0') # 5th day is padded


    def test_strict_padding_daily(self):
        """Test daily data with missing points (padding with 0)"""
        start_date = "2024-01-01"
        end_date = "2024-01-05" # 5 days
        
        # Only provide 2 points
        decrypted_all = "100,100"
        decrypted_wise = "50,50"
        decrypted_pc = "50,50"
        
        data = {"data": {"generalRatio": [{"all": {"avg": 100}}]}}
        
        daily_data, _ = self.processor.process_search_index_daily_data(
            data, {}, "test", 0, "test", start_date, end_date, 
            decrypted_all, decrypted_wise, decrypted_pc
        )
        
        self.assertEqual(len(daily_data), 5) # Should strictly be 5 days
        self.assertEqual(daily_data[0]['PC+移动指数'], '100')
        self.assertEqual(daily_data[2]['PC+移动指数'], '0') # 3rd day should be 0 (padded)
        self.assertEqual(daily_data[4]['PC+移动指数'], '0') # 5th day should be 0 (padded)

    def test_duration_based_detection(self):
        """Test weekly detection based on > 365 days duration"""
        start_date = "2024-01-01"
        end_date = "2025-01-02"  # 367 days > 365
        
        # Even if points ratio isn't extremely skewed (hypothetically),
        # implementation forces weekly for > 365 days.
        # Let's say we have ~52 points (weekly)
        decrypted_all = ",".join(["100"] * 53)
        decrypted_wise = ",".join(["50"] * 53)
        decrypted_pc = ",".join(["50"] * 53)
        
        data = {"data": {"generalRatio": [{"all": {"avg": 100}}]}}
        
        daily_data, _ = self.processor.process_search_index_daily_data(
            data, {}, "test", 0, "test", start_date, end_date, 
            decrypted_all, decrypted_wise, decrypted_pc
        )
        
        # Should be weekly
        self.assertEqual(daily_data[0]['数据类型'], '周度')
        self.assertEqual(daily_data[0]['数据间隔(天)'], 7)


if __name__ == '__main__':
    unittest.main()
