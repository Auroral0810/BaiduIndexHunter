"""
任务调度器模块
负责任务的创建、管理和调度
"""
import os
import sys
import json
import time
import uuid
import threading
from datetime import datetime
from queue import Queue, PriorityQueue

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import log
from db.mysql_manager import MySQLManager
from scheduler.task_executor import task_executor


class TaskScheduler:
    """任务调度器，负责任务的创建、管理和调度"""
    
    def __init__(self):
        """初始化任务调度器"""
        self.mysql = MySQLManager()
        self.task_queue = PriorityQueue()  # 优先级队列，用于存储待执行的任务
        self.max_concurrent_tasks = 3  # 最大并发任务数
        self.running_tasks = {}  # 记录正在运行的任务 {task_id: thread}
        self.is_running = False  # 调度器是否正在运行
        self.scheduler_thread = None  # 调度器线程
    
    def start(self):
        """启动任务调度器"""
        if self.is_running:
            log.warning("任务调度器已经在运行中")
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        log.info("任务调度器已启动")
        
        # 加载未完成的任务
        self._load_pending_tasks()
    
    def stop(self):
        """停止任务调度器"""
        if not self.is_running:
            log.warning("任务调度器未在运行")
            return
        
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        log.info("任务调度器已停止")
    
    def create_task(self, task_type, parameters, task_name=None, created_by=None, priority=5):
        """
        创建任务
        :param task_type: 任务类型
        :param parameters: 任务参数
        :param task_name: 任务名称
        :param created_by: 创建者
        :param priority: 优先级，范围1-10，数字越大优先级越高
        :return: 任务ID
        """
        # 生成任务ID
        task_id = self._generate_task_id()
        
        # 如果没有提供任务名称，使用任务类型作为名称
        if not task_name:
            task_name = f"{task_type}_{task_id}"
        
        # 将参数转为JSON字符串
        if isinstance(parameters, dict):
            parameters_json = json.dumps(parameters, ensure_ascii=False)
        else:
            parameters_json = parameters
        
        # 创建任务记录
        query = """
            INSERT INTO spider_tasks (
                task_id, task_name, task_type, status, parameters, 
                progress, total_items, completed_items, failed_items,
                create_time, created_by, priority
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        now = datetime.now()
        values = (
            task_id, task_name, task_type, 'pending', parameters_json,
            0, 0, 0, 0, now, created_by, priority
        )
        
        self.mysql.execute_query(query, values)
        
        log.info(f"创建任务成功: {task_id}, 类型: {task_type}, 优先级: {priority}")
        
        # 将任务加入队列
        self._add_task_to_queue(task_id, -priority)  # 优先级取负值，数值越小优先级越高
        
        return task_id
    
    def start_task(self, task_id):
        """
        启动任务
        :param task_id: 任务ID
        :return: 是否成功
        """
        # 检查任务状态
        task = self.get_task(task_id)
        if not task:
            log.warning(f"任务不存在: {task_id}")
            return False
        
        status = task['status']
        
        # 只有待处理或暂停状态的任务才能启动
        if status not in ['pending', 'paused']:
            log.warning(f"任务状态不允许启动: {task_id}, 当前状态: {status}")
            return False
        
        # 更新任务状态为待处理
        query = "UPDATE spider_tasks SET status = 'pending', update_time = %s WHERE task_id = %s"
        self.mysql.execute_query(query, (datetime.now(), task_id))
        
        # 将任务加入队列
        self._add_task_to_queue(task_id, 0)  # 默认优先级为0
        
        log.info(f"任务已加入队列: {task_id}")
        return True
    
    def pause_task(self, task_id):
        """
        暂停任务
        :param task_id: 任务ID
        :return: 是否成功
        """
        # 检查任务状态
        task = self.get_task(task_id)
        if not task:
            log.warning(f"任务不存在: {task_id}")
            return False
        
        status = task['status']
        
        # 只有运行中的任务才能暂停
        if status != 'running':
            log.warning(f"任务状态不允许暂停: {task_id}, 当前状态: {status}")
            return False
        
        # 停止任务执行
        task_executor.stop_task(task_id)
        
        # 更新任务状态为暂停
        query = "UPDATE spider_tasks SET status = 'paused', update_time = %s WHERE task_id = %s"
        self.mysql.execute_query(query, (datetime.now(), task_id))
        
        log.info(f"任务已暂停: {task_id}")
        return True
    
    def resume_task(self, task_id):
        """
        恢复任务
        :param task_id: 任务ID
        :return: 是否成功
        """
        # 与启动任务相同
        return self.start_task(task_id)
    
    def cancel_task(self, task_id):
        """
        取消任务
        :param task_id: 任务ID
        :return: 是否成功
        """
        # 检查任务状态
        task = self.get_task(task_id)
        if not task:
            log.warning(f"任务不存在: {task_id}")
            return False
        
        status = task['status']
        
        # 已完成或已失败的任务不能取消
        if status in ['completed', 'failed', 'cancelled']:
            log.warning(f"任务状态不允许取消: {task_id}, 当前状态: {status}")
            return False
        
        # 如果任务正在运行，先停止
        if status == 'running':
            task_executor.stop_task(task_id)
        
        # 更新任务状态为取消
        query = "UPDATE spider_tasks SET status = 'cancelled', update_time = %s, end_time = %s WHERE task_id = %s"
        now = datetime.now()
        self.mysql.execute_query(query, (now, now, task_id))
        
        log.info(f"任务已取消: {task_id}")
        return True
    
    def get_task(self, task_id):
        """
        获取任务详情
        :param task_id: 任务ID
        :return: 任务详情
        """
        query = "SELECT * FROM spider_tasks WHERE task_id = %s"
        task = self.mysql.fetch_one(query, (task_id,))
        
        if task and 'parameters' in task and task['parameters']:
            try:
                task['parameters'] = json.loads(task['parameters'])
            except:
                pass
        
        if task and 'checkpoint_path' in task and task['checkpoint_path']:
            try:
                task['checkpoint_path'] = json.loads(task['checkpoint_path'])
            except:
                pass
        
        if task and 'output_files' in task and task['output_files']:
            try:
                task['output_files'] = json.loads(task['output_files'])
            except:
                pass
        
        return task
    
    def list_tasks(self, status=None, task_type=None, created_by=None, limit=10, offset=0):
        """
        获取任务列表
        :param status: 任务状态
        :param task_type: 任务类型
        :param created_by: 创建者
        :param limit: 每页数量
        :param offset: 偏移量
        :return: 任务列表
        """
        # 构建查询条件
        conditions = []
        values = []
        
        if status:
            conditions.append("status = %s")
            values.append(status)
        
        if task_type:
            conditions.append("task_type = %s")
            values.append(task_type)
        
        if created_by:
            conditions.append("created_by = %s")
            values.append(created_by)
        
        # 构建查询语句
        query = "SELECT task_id ,task_type,status,parameters,progress,create_time FROM spider_tasks"
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY create_time DESC LIMIT %s OFFSET %s"
        values.extend([limit, offset])
        
        # 执行查询
        tasks = self.mysql.fetch_all(query, values)
        
        return tasks
    
    def count_tasks(self, status=None, task_type=None, created_by=None):
        """
        获取任务数量
        :param status: 任务状态
        :param task_type: 任务类型
        :param created_by: 创建者
        :return: 任务数量
        """
        # 构建查询条件
        conditions = []
        values = []
        
        if status:
            conditions.append("status = %s")
            values.append(status)
        
        if task_type:
            conditions.append("task_type = %s")
            values.append(task_type)
        
        if created_by:
            conditions.append("created_by = %s")
            values.append(created_by)
        
        # 构建查询语句
        query = "SELECT COUNT(*) AS count FROM spider_tasks"
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # 执行查询
        result = self.mysql.fetch_one(query, values)
        
        return result['count'] if result else 0
    
    def get_task_logs(self, task_id, limit=100, offset=0):
        """
        获取任务日志
        :param task_id: 任务ID
        :param limit: 每页数量
        :param offset: 偏移量
        :return: 日志列表
        """
        query = """
            SELECT * FROM task_logs 
            WHERE task_id = %s 
            ORDER BY timestamp DESC 
            LIMIT %s OFFSET %s
        """
        
        logs = self.mysql.fetch_all(query, (task_id, limit, offset))
        
        return logs
    
    def get_task_statistics(self, task_id):
        """
        获取任务统计数据
        :param task_id: 任务ID
        :return: 统计数据
        """
        query = "SELECT * FROM task_statistics WHERE task_id = %s"
        statistics = self.mysql.fetch_all(query, (task_id,))
        
        return statistics
    
    def _generate_task_id(self):
        """
        生成任务ID
        :return: 任务ID
        """
        # 使用时间戳和UUID生成唯一ID
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = uuid.uuid4().hex[:8]
        
        return f"{timestamp}_{random_str}"
    
    def _add_task_to_queue(self, task_id, priority=0):
        """
        将任务加入队列
        :param task_id: 任务ID
        :param priority: 优先级，数值越小优先级越高
        """
        self.task_queue.put((priority, task_id))
        log.debug(f"任务已加入队列: {task_id}, 优先级: {priority}")
    
    def _load_pending_tasks(self):
        """加载未完成的任务到队列"""
        try:
            # 查询所有待处理和暂停的任务
            query = "SELECT task_id FROM spider_tasks WHERE status IN ('pending', 'paused')"
            tasks = self.mysql.fetch_all(query)
            
            if not tasks:
                log.info("没有待处理的任务")
                return
            
            # 将任务加入队列
            for task in tasks:
                task_id = task['task_id']
                self._add_task_to_queue(task_id)
            
            log.info(f"已加载 {len(tasks)} 个待处理任务")
            
        except Exception as e:
            log.error(f"加载待处理任务失败: {e}")
    
    def _scheduler_loop(self):
        """调度器主循环"""
        log.info("调度器主循环已启动")
        
        while self.is_running:
            try:
                # 检查是否有空闲的执行槽
                if len(self.running_tasks) >= self.max_concurrent_tasks:
                    # 清理已完成的任务
                    self._cleanup_finished_tasks()
                    
                    # 如果仍然没有空闲槽，等待一段时间后继续
                    if len(self.running_tasks) >= self.max_concurrent_tasks:
                        time.sleep(1)
                        continue
                
                # 尝试获取一个任务，不阻塞
                try:
                    priority, task_id = self.task_queue.get(block=False)
                except Exception:
                    # 队列为空，等待一段时间后继续
                    time.sleep(1)
                    continue
                
                # 检查任务状态
                task = self.get_task(task_id)
                if not task:
                    log.warning(f"任务不存在: {task_id}")
                    self.task_queue.task_done()
                    continue
                
                status = task['status']
                
                # 只处理待处理状态的任务
                if status != 'pending':
                    log.warning(f"任务状态不是待处理: {task_id}, 当前状态: {status}")
                    self.task_queue.task_done()
                    continue
                
                # 启动任务执行线程
                self._execute_task(task)
                self.task_queue.task_done()
                
            except Exception as e:
                log.error(f"调度器循环异常: {e}")
                time.sleep(1)
    
    def _execute_task(self, task):
        """
        执行任务
        :param task: 任务信息
        """
        task_id = task['task_id']
        task_type = task['task_type']
        parameters = task['parameters']
        checkpoint_path = task.get('checkpoint_path')
        
        # 更新任务状态为运行中
        query = """
            UPDATE spider_tasks 
            SET status = 'running', update_time = %s, start_time = COALESCE(start_time, %s)
            WHERE task_id = %s
        """
        now = datetime.now()
        self.mysql.execute_query(query, (now, now, task_id))
        
        # 创建执行线程
        thread = threading.Thread(
            target=self._task_thread,
            args=(task_id, task_type, parameters, checkpoint_path)
        )
        thread.daemon = True
        
        # 记录任务线程
        self.running_tasks[task_id] = thread
        
        # 启动线程
        thread.start()
        
        log.info(f"任务开始执行: {task_id}")
    
    def _task_thread(self, task_id, task_type, parameters, checkpoint_path):
        """
        任务执行线程
        :param task_id: 任务ID
        :param task_type: 任务类型
        :param parameters: 任务参数
        :param checkpoint_path: 断点续传数据
        """
        try:
            # 执行任务
            task_executor.execute_task(task_id, task_type, parameters, checkpoint_path)
        except Exception as e:
            log.error(f"任务执行异常: {task_id}, 错误: {e}")
            
            # 更新任务状态为失败
            query = """
                UPDATE spider_tasks 
                SET status = 'failed', error_message = %s, update_time = %s, end_time = %s
                WHERE task_id = %s
            """
            now = datetime.now()
            self.mysql.execute_query(query, (str(e), now, now, task_id))
    
    def _cleanup_finished_tasks(self):
        """清理已完成的任务线程"""
        finished_tasks = []
        
        for task_id, thread in self.running_tasks.items():
            if not thread.is_alive():
                finished_tasks.append(task_id)
        
        for task_id in finished_tasks:
            del self.running_tasks[task_id]
            log.debug(f"清理已完成的任务线程: {task_id}")
    
    def update_task_checkpoint(self, task_id, checkpoint_path):
        """
        更新任务的断点续传数据
        :param task_id: 任务ID
        :param checkpoint_path: 断点续传数据
        :return: 是否成功
        """
        try:
            # 如果checkpoint_path是字符串，尝试解析为JSON对象
            if isinstance(checkpoint_path, str):
                try:
                    checkpoint_path = json.loads(checkpoint_path)
                except:
                    pass
            
            # 如果checkpoint_path是字典，转换为JSON字符串
            if isinstance(checkpoint_path, dict):
                checkpoint_path = json.dumps(checkpoint_path, ensure_ascii=False)
            
            # 更新数据库中的断点续传数据
            query = "UPDATE spider_tasks SET checkpoint_path = %s, update_time = %s WHERE task_id = %s"
            self.mysql.execute_query(query, (checkpoint_path, datetime.now(), task_id))
            
            log.info(f"更新任务断点续传数据成功: {task_id}")
            return True
        except Exception as e:
            log.error(f"更新任务断点续传数据失败: {e}")
            return False


# 创建任务调度器实例
task_scheduler = TaskScheduler()
