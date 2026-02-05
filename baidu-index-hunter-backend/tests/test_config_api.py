
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
        # 手动设置环境变量以避免干扰
        os.environ['FLASK_ENV'] = 'testing'
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """清理测试环境"""
        self.app_context.pop()

    @patch('src.services.config_service.config_manager.get_all_sorted')
    def test_list_configs(self, mock_get_all):
        """测试获取配置列表"""
        # 模拟返回数据
        mock_get_all.return_value = {
            "api.port": 5001,
            "spider.timeout": 10
        }
        
        response = self.client.get('/api/config/list')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['code'], 10000)
        self.assertEqual(data['data']['api.port'], 5001)
        mock_get_all.assert_called_once()

    @patch('src.services.config_service.config_manager.set')
    def test_set_config(self, mock_set):
        """测试设置单个配置项"""
        mock_set.return_value = True
        
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
        mock_set.assert_called_once_with("test.unit_test_key", "unit_test_value")

    @patch('src.services.config_service.config_manager.batch_set')
    def test_batch_set_config(self, mock_batch_set):
        """测试批量设置配置项 (验证 RootModel 是否支持扁平字典)"""
        mock_batch_set.return_value = (2, [])
        
        # 扁平字典 payload (之前报错 configs: Field required 的根源)
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
        # 验证 service 是否收到了正确的扁平字典
        mock_batch_set.assert_called_once_with(payload)

    @patch('src.services.config_service.config_manager.refresh_cache')
    def test_refresh_config(self, mock_refresh):
        """测试刷新缓存"""
        response = self.client.post('/api/config/refresh')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['code'], 10000)
        mock_refresh.assert_called_once()

if __name__ == '__main__':
    unittest.main()
