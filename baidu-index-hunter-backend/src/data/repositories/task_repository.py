"""
任务仓储类
处理爬虫任务的数据库操作
"""
from typing import List, Optional
from sqlmodel import select, col
from src.data.database import session_scope
from src.data.repositories.base_repository import BaseRepository
from src.data.models.task import SpiderTaskModel

class TaskRepository(BaseRepository[SpiderTaskModel]):
    def __init__(self):
        super().__init__(SpiderTaskModel)

    def get_paused_tasks(self, limit: int = 10) -> List[SpiderTaskModel]:
        """获取最近暂停的任务"""
        with session_scope() as session:
            statement = select(SpiderTaskModel).where(
                SpiderTaskModel.status == 'paused'
            ).order_by(col(SpiderTaskModel.update_time).desc()).limit(limit)
            return session.exec(statement).all()

    def get_by_task_id(self, task_id: str) -> Optional[SpiderTaskModel]:
        """根据 task_id 获取任务 (注意: id 是自增主键，task_id 是业务ID)"""
        with session_scope() as session:
            statement = select(SpiderTaskModel).where(SpiderTaskModel.task_id == task_id)
            return session.exec(statement).first()

# 全局单例
task_repo = TaskRepository()
