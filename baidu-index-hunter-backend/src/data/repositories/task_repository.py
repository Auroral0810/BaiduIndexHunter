"""
任务仓储类
处理爬虫任务的数据库操作
"""
import json
from typing import List, Optional, Dict, Union
from datetime import datetime
from sqlmodel import select, col, func
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

    def list_tasks(self, status: Optional[str] = None, task_type: Optional[str] = None, 
                   created_by: Optional[str] = None, limit: int = 10, offset: int = 0) -> List[SpiderTaskModel]:
        """获取任务列表 (支持筛选)"""
        with session_scope() as session:
            statement = select(SpiderTaskModel)
            
            if status:
                statement = statement.where(SpiderTaskModel.status == status)
            if task_type:
                statement = statement.where(SpiderTaskModel.task_type == task_type)
            if created_by:
                statement = statement.where(SpiderTaskModel.created_by == created_by)
                
            statement = statement.order_by(col(SpiderTaskModel.create_time).desc())
            statement = statement.offset(offset).limit(limit)
            
            return session.exec(statement).all()

    def count_tasks(self, status: Optional[str] = None, task_type: Optional[str] = None, 
                    created_by: Optional[str] = None, start_time: Optional[datetime] = None) -> int:
        """统计任务总数 (支持筛选)"""
        with session_scope() as session:
            statement = select(func.count(SpiderTaskModel.id))
            
            if status:
                statement = statement.where(SpiderTaskModel.status == status)
            if task_type:
                statement = statement.where(SpiderTaskModel.task_type == task_type)
            if created_by:
                statement = statement.where(SpiderTaskModel.created_by == created_by)
            if start_time:
                statement = statement.where(SpiderTaskModel.create_time >= start_time)
                
            return session.exec(statement).one() or 0

    def get_task_counts_by_status(self, start_time: Optional[datetime] = None) -> List[Dict]:
        """按状态统计任务数"""
        with session_scope() as session:
            statement = select(SpiderTaskModel.status, func.count(SpiderTaskModel.id)).group_by(SpiderTaskModel.status)
            if start_time:
                statement = statement.where(SpiderTaskModel.create_time >= start_time)
            results = session.exec(statement).all()
            return [{"status": r[0], "count": r[1]} for r in results]

    def get_task_counts_by_type(self, start_time: Optional[datetime] = None) -> List[Dict]:
        """按类型统计任务数"""
        with session_scope() as session:
            statement = select(SpiderTaskModel.task_type, func.count(SpiderTaskModel.id)).group_by(SpiderTaskModel.task_type)
            if start_time:
                statement = statement.where(SpiderTaskModel.create_time >= start_time)
            results = session.exec(statement).all()
            return [{"task_type": r[0], "count": r[1]} for r in results]

    def get_daily_task_counts(self, start_time: Optional[datetime] = None) -> List[Dict]:
        """按日期统计任务数"""
        with session_scope() as session:
            # MySQL specific: DATE(create_time)
            date_col = func.date(SpiderTaskModel.create_time)
            statement = select(date_col, func.count(SpiderTaskModel.id)).group_by(date_col).order_by(date_col)
            if start_time:
                statement = statement.where(SpiderTaskModel.create_time >= start_time)
            results = session.exec(statement).all()
            return [{"date": r[0].strftime('%Y-%m-%d') if r[0] else None, "count": r[1]} for r in results]

    def update_task_progress(self, task_id: str, status: str, progress: Optional[float] = None, 
                             completed_items: Optional[int] = None, failed_items: Optional[int] = None,
                             total_items: Optional[int] = None, start_time: Optional[datetime] = None,
                             checkpoint_path: Optional[str] = None, output_files: Optional[Union[List[str], str]] = None,
                             error_message: Optional[str] = None):
        """更新任务进度和状态 (业务逻辑封装)"""
        with session_scope() as session:
            statement = select(SpiderTaskModel).where(SpiderTaskModel.task_id == task_id)
            task = session.exec(statement).first()
            if not task:
                return False
            
            task.status = status
            task.update_time = datetime.now()
            if progress is not None:
                task.progress = progress
            if completed_items is not None:
                task.completed_items = completed_items
            if failed_items is not None:
                task.failed_items = failed_items
            if total_items is not None:
                task.total_items = total_items
            if start_time is not None:
                task.start_time = start_time
            if checkpoint_path is not None:
                task.checkpoint_path = checkpoint_path
            if output_files is not None:
                # 兼容列表格式，转换为 JSON 字符串
                if isinstance(output_files, (list, dict)):
                    task.output_files = json.dumps(output_files, ensure_ascii=False)
                else:
                    task.output_files = output_files
            if error_message:
                task.error_message = error_message
            
            if status in ('completed', 'failed'):
                task.end_time = datetime.now()
                
            session.add(task)
            session.commit()
            return True

# 全局单例
task_repo = TaskRepository()
