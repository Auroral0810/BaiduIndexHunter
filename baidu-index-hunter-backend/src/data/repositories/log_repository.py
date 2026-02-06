"""
任务日志仓储类
处理任务运行日志的数据库操作
"""
import json
from datetime import datetime
from typing import List, Optional, Any, Dict
from sqlmodel import select, col, desc
from src.data.database import session_scope
from src.data.models.log import TaskLogModel

class LogRepository:
    """任务日志仓储"""
    
    def add_log(self, task_id: str, log_level: str, message: str, details: Optional[Dict] = None):
        """
        记录一条任务日志
        :param task_id: 任务ID
        :param log_level: 日志级别 (info, warning, error, debug)
        :param message: 日志消息
        :param details: 详细信息 (字典形式，自动转JSON)
        """
        with session_scope() as session:
            log_item = TaskLogModel(
                task_id=task_id,
                log_level=log_level,
                message=message,
                details=details,
                timestamp=datetime.now()
            )
            session.add(log_item)
            session.commit()

    def get_logs_by_task(self, task_id: str, limit: int = 100, offset: int = 0) -> List[TaskLogModel]:
        """获取指定任务的日志记录"""
        with session_scope() as session:
            statement = select(TaskLogModel).where(
                TaskLogModel.task_id == task_id
            ).order_by(desc(TaskLogModel.timestamp)).offset(offset).limit(limit)
            
            return session.exec(statement).all()

    def delete_logs_by_task(self, task_id: str):
        """删除指定任务的所有日志"""
        with session_scope() as session:
            statement = select(TaskLogModel).where(TaskLogModel.task_id == task_id)
            results = session.exec(statement).all()
            for item in results:
                session.delete(item)
            session.commit()

# 全局单例
log_repo = LogRepository()
