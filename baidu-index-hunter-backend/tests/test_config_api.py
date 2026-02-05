
import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app

class TestConfigAPI(unittest.TestCase):
    """系统配置 API 单元测试"""

    def setUp(self):
        """配置测试环境"""
        os.environ['FLASK_ENV'] = 'testing'
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """清理测试环境"""
        self.app_context.pop()

    @patch('src.api.v1.config_api.config_manager')
    def test_list_configs(self, mock_manager):
        """测试获取配置列表"""
        mock_manager.get_all_sorted.return_value = {
            "api.port": 5001,
            "spider.timeout": 10
        }
        
        response = self.client.get('/api/config/list')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['code'], 10000)
        self.assertEqual(data['data']['api.port'], 5001)

    @patch('src.api.v1.config_api.config_manager')
    def test_get_config(self, mock_manager):
        """测试获取单个配置项"""
        mock_manager.get.return_value = "unit_test_value"
        
        response = self.client.get('/api/config/get/test.key')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['code'], 10000)
        self.assertEqual(data['data']['value'], "unit_test_value")

    @patch('src.api.v1.config_api.config_manager')
    def test_get_config_not_found(self, mock_manager):
        """测试获取不存在的配置项"""
        mock_manager.get.return_value = None
        
        response = self.client.get('/api/config/get/non_existent')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['code'], 10101) # NOT_FOUND

    @patch('src.api.v1.config_api.config_manager')
    def test_set_config(self, mock_manager):
        """测试设置单个配置项"""
        mock_manager.set.return_value = True
        
        payload = {
            "key": "test.unit_test_key",
            "value": "unit_test_value"
        }
        
        response = self.client.post(
            '/api/config/set',
            data=json.dumps(payload),
            content_type='application/json'
        )
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['code'], 10000)

    @patch('src.api.v1.config_api.config_manager')
    def test_delete_config(self, mock_manager):
        """测试删除配置项"""
        mock_manager.delete.return_value = True
        
        response = self.client.delete('/api/config/delete/test.key')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['code'], 10000)

    @patch('src.api.v1.config_api.config_manager')
    def test_batch_set_config(self, mock_manager):
        """测试批量设置配置项"""
        mock_manager.batch_set.return_value = (2, [])
        
        payload = {
            "test.batch1": "v1",
            "test.batch2": 100
        }
        
        response = self.client.post(
            '/api/config/batch_set',
            data=json.dumps(payload),
            content_type='application/json'
        )
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['code'], 10000)

    @patch('src.api.v1.config_api.config_manager')
    def test_refresh_config(self, mock_manager):
        """测试刷新缓存"""
        response = self.client.post('/api/config/refresh')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['code'], 10000)
        mock_manager.refresh_cache.assert_called_once()

if __name__ == '__main__':
    unittest.main()
