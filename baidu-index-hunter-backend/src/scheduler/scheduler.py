"""
任务调度器模块
负责任务的创建、管理和调度
"""
import time
import uuid
import threading
import json
from datetime import datetime
from queue import PriorityQueue
import traceback
from typing import Dict, Any, Optional

from src.core.logger import log
from src.scheduler.executor import task_executor
from src.data.repositories.task_repository import task_repo
from src.data.models.task import SpiderTaskModel, TaskQueueModel
from src.data.database import session_scope
from sqlmodel import select


class TaskScheduler:
    """任务调度器，负责任务的创建、管理和调度"""
    
    def __init__(self):
        """初始化任务调度器"""
        self.task_queue = PriorityQueue()  # 优先级队列，用于存储待执行的任务
        self.max_concurrent_tasks = 20  # 最大并发任务数
        self.running_tasks = {}  # 记录正在运行的任务 {task_id: thread}
        self.is_running = False  # 调度器是否正在运行
        self.scheduler_thread = None  # 调度器线程
        self.worker_threads = 16  # 工作线程数
        
        # 注意: 原有的 self.workers 似乎未被实际使用（worker线程内无逻辑），保留结构待后续扩展
        self.workers = [] 
    
    def start(self):
        """启动任务调度器"""
        try:
            # 加载待执行的任务
            self._load_pending_tasks()
            
            # 启动调度线程
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            
            log.info(f"任务调度器启动成功，最大并发数: {self.max_concurrent_tasks}")
        except Exception as e:
            log.error(f"启动任务调度器失败: {e}")
            log.error(traceback.format_exc())
    
    def stop(self):
        """停止任务调度器"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        log.info("任务调度器已停止")
    
    def create_task(self, task_type: str, parameters: Any, task_name: Optional[str] = None, 
                    created_by: Optional[str] = None, priority: int = 5) -> str:
        """
        创建任务
        :param task_type: 任务类型
        :param parameters: 任务参数
        :param task_name: 任务名称
        :param created_by: 创建者
        :param priority: 优先级
        :return: 任务ID
        """
        # 统一处理 parameters
        if isinstance(parameters, str):
            try:
                parameters = json.loads(parameters)
            except:
                parameters = {}

        # 检查是否为断点续传模式
        is_resume = parameters.get('resume', False)
        checkpoint_task_id = parameters.get('task_id') if is_resume else None
        
        task_id = None

        if is_resume and checkpoint_task_id:
            # --- 断点续传逻辑 ---
            # 尝试查找原任务
            original_task = task_repo.get_by_task_id(checkpoint_task_id)
            
            if original_task:
                log.info(f"断点续传模式：复用原有任务ID {checkpoint_task_id}")
                task_id = checkpoint_task_id
                
                # 合并参数
                merged_parameters = original_task.parameters_dict.copy()
                merged_parameters.update(parameters)
                merged_parameters['resume'] = True
                merged_parameters['task_id'] = task_id # 确保参数里也有 task_id

                # 更新原任务状态
                with session_scope() as session:
                    # 重新获取对象以绑定到当前 session
                    task_to_update = session.get(SpiderTaskModel, original_task.id)
                    if task_to_update:
                        task_to_update.status = 'pending'
                        task_to_update.parameters_dict = merged_parameters # 利用 setter 自动序列化
                        task_to_update.update_time = datetime.now()
                        task_to_update.progress = 0
                        task_to_update.error_message = None
                        session.add(task_to_update)
                        session.commit()
                
                # 更新或插入 TaskQueue
                self._upsert_task_queue(task_id, priority)
                
                # 加入内存队列
                self._add_task_to_queue(task_id, -priority)
                return task_id
            else:
                 log.warning(f"未找到原任务ID {checkpoint_task_id}，将作为新任务创建")

        # --- 新任务逻辑 ---
        if not task_id:
            task_id = self._generate_task_id()
        
        if not task_name:
            task_name = f"{task_type}_{task_id}"
            
        if isinstance(parameters, (dict, list)):
             parameters = json.dumps(parameters, ensure_ascii=False)

        # 创建任务记录
        new_task = SpiderTaskModel(
            task_id=task_id,
            task_name=task_name,
            task_type=task_type,
            status='pending',
            parameters=parameters,
            priority=priority,
            created_by=created_by,
            create_time=datetime.now()
        )
        task_repo.add(new_task)
        
        # 插入 TaskQueue
        self._upsert_task_queue(task_id, priority)
        
        log.info(f"创建任务成功: {task_id}, 类型: {task_type}")
        
        # 加入内存队列
        self._add_task_to_queue(task_id, -priority)
        
        return task_id

    def start_task(self, task_id: str) -> bool:
        """启动/恢复任务"""
        task = task_repo.get_by_task_id(task_id)
        if not task:
            log.warning(f"任务不存在: {task_id}")
            return False
            
        if task.status not in ['pending', 'paused']:
            log.warning(f"任务状态不允许启动: {task_id}, 当前状态: {task.status}")
            return False
            
        # 更新状态为 pending
        task_repo.update_task_progress(task_id, 'pending')
        
        # 确保在队列中
        self._upsert_task_queue(task_id, task.priority, status='waiting')
        self._add_task_to_queue(task_id, -task.priority) # 有可能重复添加，PriorityQueue 无去重，但 execute 时会检查状态
        
        return True

    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        task = task_repo.get_by_task_id(task_id)
        if not task or task.status != 'running':
             return False
             
        # 停止执行
        task_executor.stop_task(task_id)
        
        # 更新数据库状态
        task_repo.update_task_progress(task_id, 'paused')
        return True

    def resume_task(self, task_id: str) -> bool:
        """恢复任务 (同 start_task)"""
        return self.start_task(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = task_repo.get_by_task_id(task_id)
        if not task:
            return False
            
        if task.status in ['completed', 'failed', 'cancelled']:
            return False
            
        if task.status == 'running':
            task_executor.stop_task(task_id)
            
        task_repo.update_task_progress(task_id, 'cancelled')
        
        # 更新队列状态
        with session_scope() as session:
            statement = select(TaskQueueModel).where(TaskQueueModel.task_id == task_id)
            queue_item = session.exec(statement).first()
            if queue_item:
                queue_item.status = 'cancelled'
                queue_item.complete_time = datetime.now()
                session.add(queue_item)
                session.commit()
                
        return True

    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务详情 (兼容旧 API 返回字典)"""
        task = task_repo.get_by_task_id(task_id)
        if not task:
            return None
        return task.model_dump()
        
    def list_tasks(self, **kwargs) -> list:
        """获取任务列表 (简单封装，复杂查询应直接用 Repo)"""
        # 注意：这里暂未完全实现所有过滤参数，因为 Repo 方法 list_all 比较简单
        # 为了兼容性，返回所有任务（生产环境应分页）
        tasks = task_repo.list_all()
        # 倒序
        tasks.sort(key=lambda x: x.create_time, reverse=True)
        return [t.model_dump() for t in tasks]

    def _scheduler_loop(self):
        """调度器主循环"""
        self.is_running = True
        
        while self.is_running:
            try:
                self._cleanup_finished_tasks()
                
                # 检查并发限制
                if len(self.running_tasks) >= self.max_concurrent_tasks:
                    time.sleep(1)
                    continue
                    
                # 获取任务
                try:
                    priority, task_id = self.task_queue.get(block=False)
                except:
                    time.sleep(1)
                    continue
                    
                # 二次检查任务状态 (防止并发修改或已处理)
                task = task_repo.get_by_task_id(task_id)
                if not task or task.status != 'pending':
                    self.task_queue.task_done()
                    continue
                
                # 执行任务
                self._execute_task(task)
                self.task_queue.task_done()
                
            except Exception as e:
                log.error(f"调度器循环异常: {e}")
                time.sleep(1)

    def _execute_task(self, task: SpiderTaskModel):
        """执行具体任务"""
        # 更新状态为 running
        # 注意: executor 内部也会更新，但 scheduler 先更新以占位
        now = datetime.now()
        task_repo.update_task_progress(task.task_id, 'running')
        
        # 更新队列状态
        self._update_queue_status(task.task_id, 'processing', start_time=now)

        # 启动线程
        thread = threading.Thread(
            target=self._task_thread,
            args=(task.task_id, task.task_type, task.parameters_dict, task.checkpoint_path)
        )
        thread.daemon = True
        self.running_tasks[task.task_id] = thread
        thread.start()

    def _task_thread(self, task_id, task_type, parameters, checkpoint_path):
        """线程包装器"""
        try:
            task_executor.execute_task(task_id, task_type, parameters, checkpoint_path)
        except Exception as e:
            log.error(f"线程执行异常: {e}")
            task_repo.update_task_progress(task_id, 'failed', error_message=str(e))
        finally:
            self._update_queue_status(task_id, 'completed', complete_time=datetime.now())

    def _cleanup_finished_tasks(self):
        """清理已结束的线程"""
        # 使用 list() 复制 keys 避免运行时修改字典错误
        for task_id in list(self.running_tasks.keys()):
            thread = self.running_tasks[task_id]
            if not thread.is_alive():
                del self.running_tasks[task_id]

    def _generate_task_id(self):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = uuid.uuid4().hex[:8]
        return f"{timestamp}_{random_str}"

    def _load_pending_tasks(self):
        """应用启动时加载未完成任务"""
        # 简单实现：查询数据库中 pending/paused
        # 实际上 Repo 还没有专用 filter 方法，这里为了兼容先暂略或使用原生 SQLModel
        # 为简化，暂不自动恢复 pending 任务，依赖用户或守护进程触发 resumed (或者可自行添加 Repo 方法)
        pass

    def _upsert_task_queue(self, task_id: str, priority: int, status: str = 'waiting'):
        """插入或更新任务队列表"""
        with session_scope() as session:
            statement = select(TaskQueueModel).where(TaskQueueModel.task_id == task_id)
            queue_item = session.exec(statement).first()
            
            if queue_item:
                queue_item.status = status
                queue_item.priority = priority
                if status == 'waiting':
                    queue_item.enqueue_time = datetime.now()
                session.add(queue_item)
            else:
                new_item = TaskQueueModel(
                    task_id=task_id,
                    priority=priority,
                    status=status,
                    enqueue_time=datetime.now()
                )
                session.add(new_item)
            session.commit()

    def _update_queue_status(self, task_id: str, status: str, start_time=None, complete_time=None):
        """更新队列状态辅助"""
        with session_scope() as session:
            statement = select(TaskQueueModel).where(TaskQueueModel.task_id == task_id)
            queue_item = session.exec(statement).first()
            if queue_item:
                queue_item.status = status
                if start_time:
                    queue_item.start_time = start_time
                if complete_time:
                    queue_item.complete_time = complete_time
                session.add(queue_item)
                session.commit()

    def _add_task_to_queue(self, task_id: str, priority: int):
        """添加任务到内存队列"""
        self.task_queue.put((priority, task_id))

# 全局单例
task_scheduler = TaskScheduler()
