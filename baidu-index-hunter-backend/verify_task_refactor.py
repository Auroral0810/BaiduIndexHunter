
import sys
import os
import unittest

# Add project root to path
sys.path.append(os.getcwd())

from src.core.logger import log

class TestTaskRefactoring(unittest.TestCase):
    def test_imports(self):
        log.info("Testing Task API imports...")
        
        try:
            from src.api.v1.task_controller import task_blueprint
            log.info("Task Blueprint imported successfully.")
        except ImportError as e:
            self.fail(f"Failed to import Task Blueprint: {e}")

        try:
            from src.services.task_service import task_service
            log.info("TaskService imported successfully.")
        except ImportError as e:
            self.fail(f"Failed to import TaskService: {e}")

    def test_create_task_validation(self):
        log.info("Testing TaskService validation logic...")
        from src.services.task_service import task_service
        
        # Test invalid task type
        with self.assertRaises(ValueError):
            task_service.create_task('invalid_type', {})
            
        # Test missing params for search_index
        with self.assertRaises(ValueError):
            task_service.create_task('search_index', {'keywords': ['test']}) # Missing cities

        log.info("TaskService validation logic validated.")

if __name__ == '__main__':
    unittest.main()
