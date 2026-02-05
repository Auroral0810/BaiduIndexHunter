
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
        
        self.assertEqual(len(daily_data), 4) # Should only have 4 records
        self.assertEqual(daily_data[0]['数据类型'], '周度')
        self.assertEqual(daily_data[0]['数据间隔(天)'], 7)
        self.assertEqual(daily_data[0]['日期'], '2024-01-01')
        # Next date should be +7 days
        self.assertEqual(daily_data[1]['日期'], '2024-01-08')

if __name__ == '__main__':
    unittest.main()
