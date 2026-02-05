
import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app

class TestCookieAPI(unittest.TestCase):
    """Cookie API 单元测试"""

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

    @patch('src.api.v1.cookie_controller.cookie_service')
    def test_get_pool_status(self, mock_service):
        """测试获取Cookie池状态"""
        mock_service.get_pool_status_data.return_value = {
            'total': 10, 'available': 8, 'temp_banned': 1, 'perm_banned': 1
        }
        response = self.client.get('/api/admin/cookie/pool-status')
        data = response.get_json()
        self.assertEqual(data['code'], 10000)
        self.assertEqual(data['data']['total'], 10)

    @patch('src.api.v1.cookie_controller.cookie_service')
    def test_list_cookies(self, mock_service):
        """测试获取Cookie列表"""
        mock_service.get_cookie_list_with_pagination.return_value = {
            'items': [{'account_id': 'test_acc', 'cookies': {'BAIDUID': 'value'}}],
            'total': 1,
            'page': 1,
            'limit': 10
        }
        response = self.client.get('/api/admin/cookie/list?page=1&limit=10')
        data = response.get_json()
        
        # Controller structure: { code: 10000, data: { data: result['items'], ... } }
        self.assertEqual(data['code'], 10000)
        self.assertEqual(len(data['data']['data']), 1)
        self.assertEqual(data['data']['total'], 1)

    @patch('src.api.v1.cookie_controller.cookie_service')
    def test_add_cookie(self, mock_service):
        """测试添加Cookie"""
        mock_service.add_cookie.return_value = True
        payload = {
            "account_id": "test_acc",
            "cookie_data": {"BAIDUID": "test_value"},
            "expire_days": 30
        }
        response = self.client.post('/api/admin/cookie/add', 
                                  data=json.dumps(payload), 
                                  content_type='application/json')
        data = response.get_json()
        self.assertEqual(data['code'], 10000)

    @patch('src.api.v1.cookie_controller.cookie_service')
    def test_delete_cookie(self, mock_service):
        """测试删除Cookie"""
        mock_service.delete_by_account_id.return_value = 1
        response = self.client.delete('/api/admin/cookie/delete/test_acc')
        data = response.get_json()
        self.assertEqual(data['code'], 10000)
        self.assertEqual(data['data']['deleted_count'], 1)

    @patch('src.api.v1.cookie_controller.cookie_service')
    def test_unban_account(self, mock_service):
        """测试解封账号"""
        mock_service.unban_account.return_value = 1
        response = self.client.post('/api/admin/cookie/unban/test_acc')
        data = response.get_json()
        self.assertEqual(data['code'], 10000)
        self.assertEqual(data['data']['unbanned_count'], 1)

    @patch('src.api.v1.cookie_controller.cookie_service')
    def test_force_unban_account(self, mock_service):
        """测试强制解封账号"""
        mock_service.force_unban_account.return_value = 1
        response = self.client.post('/api/admin/cookie/force-unban/test_acc')
        data = response.get_json()
        self.assertEqual(data['code'], 10000)
        self.assertEqual(data['data']['unbanned_count'], 1)

    @patch('src.api.v1.cookie_controller.cookie_service')
    def test_sync_to_redis(self, mock_service):
        """测试同步到Redis"""
        mock_service.sync_to_redis.return_value = True
        response = self.client.post('/api/admin/cookie/sync-to-redis')
        data = response.get_json()
        self.assertEqual(data['code'], 10000)
        mock_service.sync_to_redis.assert_called_once()

    @patch('src.api.v1.cookie_controller.cookie_service')
    def test_test_availability(self, mock_service):
        """测试全量可用性测试"""
        mock_service.test_cookies_availability.return_value = {
            "valid_accounts": ["acc1"], "banned_accounts": [], "not_login_accounts": [],
            "total_tested": 1, "valid_count": 1, "banned_count": 0, "not_login_count": 0
        }
        response = self.client.post('/api/admin/cookie/test-availability')
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['code'], 10000)
        self.assertEqual(data['data']['valid_count'], 1)

    @patch('src.api.v1.cookie_controller.cookie_service')
    def test_test_account_availability(self, mock_service):
        mock_service.test_account_cookie_availability.return_value = {
            "account_id": "test_acc", "status": 0, "message": "Cookie正常", "is_valid": True, "action_taken": "无"
        }
        response = self.client.post('/api/admin/cookie/test-account-availability/test_acc')
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['code'], 10000)
        self.assertEqual(data['data']['account_id'], "test_acc")
        self.assertTrue(data['data']['is_valid'])

    @patch('src.api.v1.cookie_controller.cookie_service')
    def test_update_ab_sr(self, mock_service):
        """测试更新ab_sr"""
        mock_service.update_ab_sr_for_all_accounts.return_value = 3
        response = self.client.post('/api/admin/cookie/update-ab-sr')
        data = response.get_json()
        self.assertEqual(data['code'], 10000)
        self.assertEqual(data['data']['updated_count'], 3)

    @patch('src.api.v1.cookie_controller.cookie_service')
    def test_get_cookie_usage(self, mock_service):
        """测试获取使用统计"""
        mock_service.get_cookie_usage.return_value = [{'date': '2025-01-01', 'count': 10}]
        response = self.client.get('/api/admin/cookie/usage')
        data = response.get_json()
        self.assertEqual(data['code'], 10000)
        self.assertEqual(len(data['data']), 1)

if __name__ == '__main__':
    unittest.main()
