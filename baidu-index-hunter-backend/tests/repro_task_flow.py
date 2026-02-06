
import sys
import os
import time
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scheduler.scheduler import task_scheduler
from src.data.repositories.task_repository import task_repo

def repro_flow():
    task_type = 'search_index'
    parameters = {'keywords': ['test'], 'cities': ['0'], 'resume': False}
    
    print("Step 1: Creating task...")
    task_id = task_scheduler.create_task(
        task_type=task_type,
        parameters=parameters,
        task_name="Repro Task",
        priority=5
    )
    print(f"Task created with ID: {task_id}")
    
    print("Step 2: Checking DB immediately...")
    task = task_repo.get_by_task_id(task_id)
    if task:
        print(f"SUCCESS: Task found in DB. Status: {task.status}")
    else:
        print("FAILED: Task NOT found in DB!")
        return
        
    print("Step 3: Updating progress (Simulating Crawler)...")
    success = task_repo.update_task_progress(task_id, status='running', progress=10.0)
    if success:
        print("SUCCESS: Progress updated.")
    else:
        print("FAILED: Could not update progress - Task not found!")

if __name__ == "__main__":
    repro_flow()
