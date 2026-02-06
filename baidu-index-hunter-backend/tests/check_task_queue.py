
import sys
import os
from datetime import datetime
from sqlmodel import select, col

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.models.task import TaskQueueModel
from src.data.database import session_scope

def check_queue(task_id):
    print(f"Checking task_queue for task_id: {task_id}")
    with session_scope() as session:
        statement = select(TaskQueueModel).where(TaskQueueModel.task_id == task_id)
        item = session.exec(statement).first()
        if item:
            print(f"FOUND in task_queue: {item.model_dump()}")
        else:
            print("NOT FOUND in task_queue.")

if __name__ == "__main__":
    task_id = sys.argv[1] if len(sys.argv) > 1 else "20260207003816_0d88895a"
    check_queue(task_id)
