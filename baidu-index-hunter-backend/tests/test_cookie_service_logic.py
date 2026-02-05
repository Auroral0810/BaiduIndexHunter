import unittest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timedelta
import json
import execjs

# Set environment variable for testing
import os
os.environ['FLASK_ENV'] = 'testing'

from src.services.cookie_service import CookieManager

class TestCookieServiceLogic(unittest.TestCase):
    def setUp(self):
        # Patch the repo and redis client in __init__ to avoid real connections
        with patch('src.services.cookie_service.cookie_repo'), \
             patch('src.services.cookie_service.redis.Redis'), \
             patch('src.services.cookie_service.AbSrUpdater'):
            self.service = CookieManager()
            self.service.repo = MagicMock()
            self.service.redis_client = MagicMock()

    def test_get_cookie_list_with_pagination_logic(self):
        """Test the logic for pagination and data assembly in the service layer."""
        # 1. Mock inputs
        mock_ids = ["acc_1", "acc_2", "acc_3"]
        self.service.repo.get_account_ids_by_filter.return_value = mock_ids
        
        # Mock models for these accounts
        mock_cookie_1 = MagicMock(account_id="acc_1", cookie_name="BAIDUID", cookie_value="val1", is_available=True, is_permanently_banned=False, temp_ban_until=None, expire_time=None)
        mock_cookie_2 = MagicMock(account_id="acc_2", cookie_name="BAIDUID", cookie_value="val2", is_available=False, is_permanently_banned=False, temp_ban_until=datetime.now()+timedelta(hours=1), expire_time=None)
        
        self.service.repo.get_cookies_by_account_ids.return_value = [mock_cookie_1, mock_cookie_2]

        # 2. Call service method (page 1, limit 2)
        result = self.service.get_cookie_list_with_pagination(page=1, limit=2)

        # 3. Assertions
        self.assertEqual(result['total'], 3)
        self.assertEqual(len(result['items']), 2) # Only acc_1 and acc_2 have cookies in our mock
        self.assertEqual(result['items'][0]['account_id'], "acc_1")
        self.assertTrue(result['items'][0]['is_available'])
        self.assertEqual(result['items'][1]['account_id'], "acc_2")
        self.assertFalse(result['items'][1]['is_available'])
        self.assertIsNotNone(result['items'][1]['temp_ban_until'])

    def test_sync_to_redis_logic(self):
        """Test the logic that groups cookies and saves them to Redis."""
        # 1. Mock available cookies
        mock_c1 = MagicMock(account_id="acc_1", cookie_name="c1", cookie_value="v1", is_available=True, is_permanently_banned=False, temp_ban_until=None)
        mock_c2 = MagicMock(account_id="acc_1", cookie_name="c2", cookie_value="v2", is_available=True, is_permanently_banned=False, temp_ban_until=None)
        self.service.repo.get_available_cookies.return_value = [mock_c1, mock_c2]
        
        # 2. Call sync
        success = self.service.sync_to_redis()
        
        # 3. Assertions
        self.assertTrue(success)
        self.service.redis_client.delete.assert_called()
        # Verify save called for acc_1
        self.service.redis_client.hset.assert_any_call(
            self.service.REDIS_COOKIES_KEY, "acc_1", unittest.mock.ANY
        )
        # Check specific count setting
        self.service.redis_client.set.assert_called_with(self.service.REDIS_COOKIE_COUNT_KEY, 1)

    def test_add_cookie_parsing(self):
        """Test that add_cookie correctly handles both string and dict inputs."""
        self.service.repo.upsert_cookies.return_value = True
        self.service.redis_client.get.return_value = "5"
        
        # Case 1: Dict input
        self.service.add_cookie("test_acc", {"k": "v"})
        self.service.repo.upsert_cookies.assert_called_with("test_acc", {"k": "v"}, unittest.mock.ANY)
        
        # Case 2: String input (JSON)
        self.service.add_cookie("test_acc", '{"k2": "v2"}')
        self.service.repo.upsert_cookies.assert_called_with("test_acc", {"k2": "v2"}, unittest.mock.ANY)
        
        # Case 3: String input (Cookie Format)
        self.service.add_cookie("test_acc", "k3=v3; k4=v4")
        self.service.repo.upsert_cookies.assert_called_with("test_acc", {"k3": "v3", "k4": "v4"}, unittest.mock.ANY)

    @patch('src.services.cookie_service.requests.get')
    @patch('src.services.cookie_service.execjs.compile')
    @patch('src.services.cookie_service.open', new_callable=mock_open, read_data='js_code')
    @patch('src.services.cookie_service.os.path.exists')
    def test_availability_success_scenario(self, mock_exists, mock_file, mock_compile, mock_requests_get):
        """Test the full availability testing flow (success case)."""
        # 1. Setup mocks
        mock_exists.return_value = True
        self.service.repo.get_available_account_ids.return_value = ["acc_success"]
        
        # Mock get_cookie_by_account_id call inside test
        mock_cookie_dict = {"BAIDUID": "valid_val"}
        mock_cookie_model = MagicMock(cookie_name="BAIDUID", cookie_value="valid_val", is_available=True, is_permanently_banned=False, temp_ban_until=None, expire_time=None)
        self.service.repo.get_cookies_by_account_id.return_value = [mock_cookie_model]
        
        # Mock JS compiler
        mock_ctx = MagicMock()
        mock_ctx.call.return_value = "mock_cipher"
        mock_compile.return_value = mock_ctx
        
        # Mock API response
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": 0}
        mock_requests_get.return_value = mock_resp

        # 2. Run test
        result = self.service.test_cookies_availability()

        # 3. Assertions
        self.assertEqual(result['valid_count'], 1)
        self.assertIn("acc_success", result['valid_accounts'])
        self.service.redis_client.hset.assert_called() # Should resync to redis

    @patch('src.services.cookie_service.requests.get')
    @patch('src.services.cookie_service.os.path.exists')
    def test_availability_banned_scenario(self, mock_exists, mock_requests_get):
        """Test the availability testing flow when an account is temporarily banned (status 10001)."""
        mock_exists.return_value = False # Skip JS part by raising error in _get_cipher_js_path
        self.service.repo.get_available_account_ids.return_value = ["acc_banned"]
        
        mock_cookie_model = MagicMock(cookie_name="c", cookie_value="v", is_available=True, is_permanently_banned=False, temp_ban_until=None, expire_time=None)
        self.service.repo.get_cookies_by_account_id.return_value = [mock_cookie_model]
        
        # Mock API response: 10001 (Temp Ban)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": 10001, "msg": "Temporarily banned"}
        mock_requests_get.return_value = mock_resp
        
        # Mock ban_account_temporarily to return an int (banned count)
        self.service.repo.ban_account_temporarily.return_value = 1

        # 2. Run test
        result = self.service.test_account_cookie_availability("acc_banned")

        # 3. Assertions
        self.assertEqual(result['status'], 10001)
        self.assertEqual(result['account_id'], "acc_banned")
        self.assertFalse(result['is_valid'])
        self.assertIn("临时封禁", result['action_taken'])

    def test_check_and_update_cookie_status_logic(self):
        """Test the logic for restoring expired temporary bans."""
        # 1. Mock repo returning some expired accounts
        self.service.repo.get_expired_temp_bans.return_value = ["acc_1"]
        self.service.repo.unlock_accounts.return_value = 1
        self.service.repo.get_available_account_ids.return_value = ["acc_1", "acc_2"]
        
        # 2. Call method
        result = self.service.check_and_update_cookie_status()
        
        # 3. Assertions
        self.assertEqual(result['updated_count'], 1)
        self.assertIn("acc_1", result['unlocked_accounts'])
        # Verify redis sync for that account
        self.service.repo.get_cookies_by_account_id.assert_called_with("acc_1")

if __name__ == '__main__':
    unittest.main()
