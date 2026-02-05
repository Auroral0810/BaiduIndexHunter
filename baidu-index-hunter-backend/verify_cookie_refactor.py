
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from src.core.logger import log

class TestCookieRefactoring(unittest.TestCase):
    def test_imports(self):
        log.info("Testing Cookie API imports...")
        
        try:
            from src.api.v1.cookie_controller import admin_cookie_bp
            log.info("Cookie Blueprint imported successfully.")
        except ImportError as e:
            self.fail(f"Failed to import Cookie Blueprint: {e}")

        try:
            from src.services.cookie_service import cookie_service
            log.info("Cookie Service imported successfully.")
        except ImportError as e:
             self.fail(f"Failed to import Cookie Service: {e}")
             
        try:
            from src.data.repositories.cookie_repository import cookie_repo
            log.info("Cookie Repository imported successfully.")
        except ImportError as e:
             self.fail(f"Failed to import Cookie Repository: {e}")

    @patch('src.data.repositories.cookie_repository.cookie_repo.get_account_ids_by_filter')
    @patch('src.data.repositories.cookie_repository.cookie_repo.get_cookies_by_account_ids')
    def test_service_pagination(self, mock_get_cookies, mock_get_ids):
        log.info("Testing Service Pagination logic...")
        from src.services.cookie_service import cookie_service
        from src.data.models.cookie import CookieModel
        
        # Mock 15 account IDs
        mock_get_ids.return_value = [f"acc_{i}" for i in range(15)]
        
        # Mock cookies for the first 10 accounts
        mock_cookies = []
        for i in range(10):
            mock_cookies.append(CookieModel(account_id=f"acc_{i}", cookie_name="BDUSS", cookie_value="test", is_available=True))
        mock_get_cookies.return_value = mock_cookies
        
        # Test page 1, limit 10
        result = cookie_service.get_cookie_list_with_pagination(page=1, limit=10)
        self.assertEqual(result['total'], 15)
        self.assertEqual(len(result['items']), 10) 
        
        # Test page 2
        mock_get_cookies.return_value = [] # Assume empty for simplicity or mock 5 items
        result = cookie_service.get_cookie_list_with_pagination(page=2, limit=10)
        self.assertEqual(result['page'], 2)
            
        log.info("Service Pagination logic validated.")

if __name__ == '__main__':
    unittest.main()
