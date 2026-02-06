
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scheduler.scheduler import task_scheduler
from src.data.repositories.task_repository import task_repo
from src.data.models.task import SpiderTaskModel

def test_update_task_checkpoint():
    task_id = "test_verify_id_123"
    checkpoint_path = "/tmp/test_checkpoint.db"
    
    print(f"Testing TaskScheduler.update_task_checkpoint for task {task_id}...")
    
    # 1. Ensure task exists in DB (Mock or real)
    task = task_repo.get_by_task_id(task_id)
    if not task:
        print("Creating dummy task for testing...")
        new_task = SpiderTaskModel(
            task_id=task_id,
            task_name="Test Task",
            task_type="search_index",
            status='pending',
            parameters="{}",
            priority=5,
            create_time=datetime.now()
        )
        task_repo.add(new_task)
    
    # 2. Call the new method
    try:
        task_scheduler.update_task_checkpoint(task_id, checkpoint_path)
        print("Successfully called update_task_checkpoint.")
    except AttributeError as e:
        print(f"FAILED: Method still missing! {e}")
        return False
    except Exception as e:
        print(f"FAILED: Unexpected error: {e}")
        return False
        
    # 3. Verify DB update
    updated_task = task_repo.get_by_task_id(task_id)
    if updated_task and updated_task.checkpoint_path == checkpoint_path:
        print("SUCCESS: Database updated correctly.")
        return True
    else:
        print(f"FAILED: Database not updated. Checkpoint path: {updated_task.checkpoint_path if updated_task else 'None'}")
        return False

if __name__ == "__main__":
    success = test_update_task_checkpoint()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
