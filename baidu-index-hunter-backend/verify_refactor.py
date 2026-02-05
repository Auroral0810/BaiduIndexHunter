
import sys
import os
import unittest

# Add project root to path
sys.path.append(os.getcwd())

from src.core.logger import log

class TestRefactoring(unittest.TestCase):
    def test_imports(self):
        log.info("Testing imports...")
        
        # 1. Config
        try:
            from src.api.v1.config_api import config_bp
            from src.services.config_service import config_manager
            log.info("Config modules imported successfully.")
        except ImportError as e:
            self.fail(f"Failed to import Config modules: {e}")

        # 2. Word Check
        try:
            from src.api.v1.word_check_controller import word_check_blueprint
            from src.services.word_check_service import word_check_service
            log.info("Word Check modules imported successfully.")
        except ImportError as e:
            self.fail(f"Failed to import Word Check modules: {e}")

        # 3. Region
        try:
            from src.api.v1.region_controller import region_blueprint
            from src.services.region_service import region_manager
            log.info("Region modules imported successfully.")
        except ImportError as e:
            self.fail(f"Failed to import Region modules: {e}")
            
        # 4. AbSr Updater
        try:
            from src.engine.crypto.ab_sr_updater import AbSrUpdater
            log.info("AbSrUpdater imported successfully.")
        except ImportError as e:
            self.fail(f"Failed to import AbSrUpdater: {e}")

    def test_service_instances(self):
        log.info("Testing service instances...")
        from src.services.config_service import config_manager
        from src.services.word_check_service import word_check_service
        from src.services.region_service import region_manager
        
        self.assertIsNotNone(config_manager)
        self.assertIsNotNone(word_check_service)
        self.assertIsNotNone(region_manager)
        log.info("Service instances verified.")

if __name__ == '__main__':
    unittest.main()
