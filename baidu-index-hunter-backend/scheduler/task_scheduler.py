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
import traceback

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
        self.max_concurrent_tasks = 20  # 最大并发任务数，增加到20
        self.running_tasks = {}  # 记录正在运行的任务 {task_id: thread}
        self.is_running = False  # 调度器是否正在运行
        self.scheduler_thread = None  # 调度器线程
        self.worker_threads = 16  # 工作线程数，增加到16
        self.workers = []  # 工作线程列表
    
    def start(self):
        """
        启动任务调度器
        """
        try:
            log.info("启动任务调度器")
            
            # 初始化表结构
            self._init_tables()
            
            # 更新历史任务的累计爬取数据条数（初次添加字段时需要）
            self._update_historical_crawled_items()
            
            # 加载待执行的任务
            self._load_pending_tasks()
            
            # 启动工作线程
            for _ in range(self.worker_threads):
                worker = threading.Thread(target=self._worker, daemon=True)
                worker.start()
                self.workers.append(worker)
            
            # 启动调度线程
            self.scheduler_thread = threading.Thread(target=self._scheduler, daemon=True)
            self.scheduler_thread.start()
            
            log.info(f"任务调度器启动成功，工作线程数: {self.worker_threads}")
        except Exception as e:
            log.error(f"启动任务调度器失败: {e}")
            log.error(traceback.format_exc())
    
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
        # 检查是否为断点续传模式
        is_resume = parameters.get('resume', False)
        checkpoint_task_id = parameters.get('task_id') if is_resume else None
        
        # 如果是断点续传模式且提供了task_id，则使用原有task_id
        if is_resume and checkpoint_task_id:
            task_id = checkpoint_task_id
            
            # 检查原任务是否存在
            check_query = "SELECT id FROM spider_tasks WHERE task_id = %s"
            task = self.mysql.fetch_one(check_query, (task_id,))
            
            if task:
                log.info(f"断点续传模式：使用原有任务ID {task_id}")
                
                # 将参数转为JSON字符串
                if isinstance(parameters, dict):
                    parameters_json = json.dumps(parameters, ensure_ascii=False)
                else:
                    parameters_json = parameters
                
                # 更新任务状态为待处理
                now = datetime.now()
                update_query = """
                    UPDATE spider_tasks 
                    SET status = 'pending', parameters = %s, update_time = %s, 
                        progress = 0, error_message = NULL
                    WHERE task_id = %s
                """
                self.mysql.execute_query(update_query, (parameters_json, now, task_id))
                
                # 检查任务是否在task_queue表中
                check_queue_query = "SELECT id FROM task_queue WHERE task_id = %s"
                queue_record = self.mysql.fetch_one(check_queue_query, (task_id,))
                
                if queue_record:
                    # 更新队列状态
                    queue_update_query = """
                        UPDATE task_queue 
                        SET status = 'waiting', priority = %s, enqueue_time = %s,
                            start_time = NULL, complete_time = NULL
                        WHERE task_id = %s
                    """
                    self.mysql.execute_query(queue_update_query, (priority, now, task_id))
                else:
                    # 添加到队列表
                    queue_insert_query = """
                        INSERT INTO task_queue (
                            task_id, priority, status, enqueue_time
                        ) VALUES (%s, %s, %s, %s)
                    """
                    queue_values = (task_id, priority, 'waiting', now)
                    self.mysql.execute_query(queue_insert_query, queue_values)
                
                # 将任务加入队列
                self._add_task_to_queue(task_id, -priority)  # 优先级取负值
                
                log.info(f"断点续传任务已更新: {task_id}, 类型: {task_type}, 优先级: {priority}")
                return task_id
            else:
                log.warning(f"未找到原任务ID {task_id}，将创建新任务")
        
        # 如果不是断点续传模式或未找到原任务，则创建新任务
        if not is_resume or not checkpoint_task_id:
            task_id = self._generate_task_id()
        else:
            task_id = checkpoint_task_id
        
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
        
        # 将任务添加到task_queue表
        queue_query = """
            INSERT INTO task_queue (
                task_id, priority, status, enqueue_time
            ) VALUES (%s, %s, %s, %s)
        """
        queue_values = (task_id, priority, 'waiting', now)
        self.mysql.execute_query(queue_query, queue_values)
        
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
        now = datetime.now()
        query = "UPDATE spider_tasks SET status = 'pending', update_time = %s WHERE task_id = %s"
        self.mysql.execute_query(query, (now, task_id))
        
        # 检查任务是否在task_queue表中存在
        check_query = "SELECT id FROM task_queue WHERE task_id = %s"
        queue_record = self.mysql.fetch_one(check_query, (task_id,))
        
        if queue_record:
            # 如果任务在队列表中存在，更新状态为waiting
            queue_update_query = """
                UPDATE task_queue 
                SET status = 'waiting' 
                WHERE task_id = %s
            """
            self.mysql.execute_query(queue_update_query, (task_id,))
        else:
            # 如果任务不在队列表中，添加到队列表
            priority = task.get('priority', 5)
            queue_insert_query = """
                INSERT INTO task_queue (
                    task_id, priority, status, enqueue_time
                ) VALUES (%s, %s, %s, %s)
            """
            queue_values = (task_id, priority, 'waiting', now)
            self.mysql.execute_query(queue_insert_query, queue_values)
        
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
        now = datetime.now()
        query = "UPDATE spider_tasks SET status = 'cancelled', update_time = %s, end_time = %s WHERE task_id = %s"
        self.mysql.execute_query(query, (now, now, task_id))
        
        # 更新task_queue表中的状态为cancelled
        queue_query = """
            UPDATE task_queue 
            SET status = 'cancelled', complete_time = %s 
            WHERE task_id = %s
        """
        self.mysql.execute_query(queue_query, (now, task_id))
        
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
            query = "SELECT task_id, priority FROM spider_tasks WHERE status IN ('pending', 'paused')"
            tasks = self.mysql.fetch_all(query)
            
            if not tasks:
                log.info("没有待处理的任务")
                return
            
            # 将任务加入队列
            now = datetime.now()
            for task in tasks:
                task_id = task['task_id']
                priority = task.get('priority', 5)
                
                # 检查任务是否在task_queue表中
                check_query = "SELECT id, status FROM task_queue WHERE task_id = %s"
                queue_record = self.mysql.fetch_one(check_query, (task_id,))
                
                if queue_record:
                    # 如果在队列表中，但状态不是waiting，更新为waiting
                    if queue_record['status'] != 'waiting':
                        update_query = "UPDATE task_queue SET status = 'waiting' WHERE task_id = %s"
                        self.mysql.execute_query(update_query, (task_id,))
                else:
                    # 如果不在队列表中，添加到队列表
                    insert_query = """
                        INSERT INTO task_queue (
                            task_id, priority, status, enqueue_time
                        ) VALUES (%s, %s, %s, %s)
                    """
                    self.mysql.execute_query(insert_query, (task_id, priority, 'waiting', now))
                
                # 将任务加入内存队列
                self._add_task_to_queue(task_id, -priority)  # 优先级取负值
            
            log.info(f"已加载 {len(tasks)} 个待处理任务")
            
        except Exception as e:
            log.error(f"加载待处理任务失败: {e}")
            log.error(traceback.format_exc())
    
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
        
        # 更新task_queue表中的状态为processing
        queue_query = """
            UPDATE task_queue 
            SET status = 'processing', start_time = %s 
            WHERE task_id = %s AND start_time IS NULL
        """
        self.mysql.execute_query(queue_query, (now, task_id))
        
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
    
    def _init_tables(self):
        """
        初始化数据库表结构
        """
        try:
            # 检查spider_statistics表是否存在total_crawled_items字段
            check_query = """
                SELECT COUNT(*) as count
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'spider_statistics' 
                AND COLUMN_NAME = 'total_crawled_items'
            """
            result = self.mysql.fetch_one(check_query)
            
            # 如果字段不存在，添加字段
            if result and result['count'] == 0:
                alter_query = """
                    ALTER TABLE spider_statistics 
                    ADD COLUMN total_crawled_items BIGINT DEFAULT 0 COMMENT '累计爬取数据条数' 
                    AFTER total_items
                """
                self.mysql.execute_query(alter_query)
                log.info("成功添加total_crawled_items字段到spider_statistics表")
        except Exception as e:
            log.error(f"初始化表结构失败: {e}")
            log.error(traceback.format_exc())
    
    def _update_historical_crawled_items(self):
        """
        更新历史任务的累计爬取数据条数
        仅在首次添加字段时执行一次
        """
        try:
            # 检查是否需要更新历史数据
            check_query = """
                SELECT COUNT(*) as count
                FROM spider_statistics
                WHERE total_crawled_items = 0 OR total_crawled_items IS NULL
            """
            result = self.mysql.fetch_one(check_query)
            
            if not result or result['count'] == 0:
                log.info("无需更新历史累计爬取数据条数")
                return
            
            log.info(f"开始更新历史累计爬取数据条数，共 {result['count']} 条记录")
            
            # 获取所有需要更新的统计记录
            stats_query = """
                SELECT id, stat_date, task_type
                FROM spider_statistics
                WHERE total_crawled_items = 0 OR total_crawled_items IS NULL
                ORDER BY stat_date
            """
            stats_records = self.mysql.fetch_all(stats_query)
            
            for stat in stats_records:
                # 计算该日期之前（含当天）的所有已完成任务的爬取条数
                crawled_items_query = """
                    SELECT SUM(completed_items) as total_crawled
                    FROM spider_tasks
                    WHERE task_type = %s 
                    AND status = 'completed'
                    AND DATE(end_time) <= %s
                """
                crawled_result = self.mysql.fetch_one(
                    crawled_items_query, 
                    (stat['task_type'], stat['stat_date'])
                )
                
                total_crawled = crawled_result['total_crawled'] if crawled_result and crawled_result['total_crawled'] else 0
                
                # 更新统计记录
                update_query = """
                    UPDATE spider_statistics
                    SET total_crawled_items = %s
                    WHERE id = %s
                """
                self.mysql.execute_query(update_query, (total_crawled, stat['id']))
                
                log.info(f"已更新 {stat['stat_date']} 的 {stat['task_type']} 任务累计爬取数据条数: {total_crawled}")
            
            log.info("历史累计爬取数据条数更新完成")
        except Exception as e:
            log.error(f"更新历史累计爬取数据条数失败: {e}")
            log.error(traceback.format_exc())
    
    def _scheduler(self):
        """调度器线程函数"""
        log.info("调度器线程已启动")
        self.is_running = True
        
        while self.is_running:
            try:
                self._scheduler_loop()
            except Exception as e:
                log.error(f"调度器线程异常: {e}")
                log.error(traceback.format_exc())
            time.sleep(1)
        
        log.info("调度器线程已停止")
    
    def _worker(self):
        """工作线程函数"""
        # log.info("工作线程已启动")
        
        while self.is_running:
            try:
                # 这里可以实现特定的工作逻辑，例如处理队列中的任务
                # 目前任务执行主要在_execute_task中通过新线程完成，这里预留接口
                time.sleep(5)
            except Exception as e:
                log.error(f"工作线程异常: {e}")
                log.error(traceback.format_exc())
        
        # log.info("工作线程已停止")
    
    def _update_spider_statistics(self, task_id, status):
        """
        更新爬虫统计数据
        :param task_id: 任务ID
        :param status: 任务状态
        :return: 是否成功
        """
        try:
            # 只处理已完成的任务
            if status != 'completed':
                return True
            
            # 获取任务信息
            query = """
                SELECT task_id, task_type, completed_items, start_time, end_time
                FROM spider_tasks
                WHERE task_id = %s
            """
            task = self.mysql.fetch_one(query, (task_id,))
            
            if not task or not task['end_time'] or not task['start_time']:
                log.warning(f"任务 {task_id} 缺少必要信息，无法更新统计数据")
                return False
            
            # 获取任务完成日期（使用结束时间的日期）
            stat_date = task['end_time'].date()
            task_type = task['task_type']
            completed_items = task['completed_items'] or 0
            
            # 检查该日期是否已有统计记录
            check_query = """
                SELECT id, total_tasks, completed_tasks, total_items, total_crawled_items
                FROM spider_statistics
                WHERE stat_date = %s AND task_type = %s
            """
            stat = self.mysql.fetch_one(check_query, (stat_date, task_type))
            
            if stat:
                # 更新现有记录
                update_query = """
                    UPDATE spider_statistics
                    SET total_tasks = total_tasks + 1,
                        completed_tasks = completed_tasks + 1,
                        total_items = total_items + %s,
                        total_crawled_items = (
                            SELECT COALESCE(SUM(completed_items), 0)
                            FROM spider_tasks
                            WHERE task_type = %s
                            AND status = 'completed'
                            AND DATE(end_time) <= %s
                        ),
                        update_time = %s
                    WHERE id = %s
                """
                self.mysql.execute_query(
                    update_query, 
                    (completed_items, task_type, stat_date, datetime.now(), stat['id'])
                )
            else:
                # 计算累计爬取数据条数
                crawled_query = """
                    SELECT COALESCE(SUM(completed_items), 0) as total_crawled
                    FROM spider_tasks
                    WHERE task_type = %s
                    AND status = 'completed'
                    AND DATE(end_time) <= %s
                """
                crawled_result = self.mysql.fetch_one(crawled_query, (task_type, stat_date))
                total_crawled_items = crawled_result['total_crawled'] if crawled_result else 0
                
                # 插入新记录
                insert_query = """
                    INSERT INTO spider_statistics
                    (stat_date, task_type, total_tasks, completed_tasks, failed_tasks, 
                     total_items, total_crawled_items, create_time, update_time)
                    VALUES (%s, %s, 1, 1, 0, %s, %s, %s, %s)
                """
                now = datetime.now()
                self.mysql.execute_query(
                    insert_query, 
                    (stat_date, task_type, completed_items, total_crawled_items, now, now)
                )
            
            return True
        except Exception as e:
            log.error(f"更新爬虫统计数据失败: {e}")
            log.error(traceback.format_exc())
            return False


# 创建任务调度器实例
task_scheduler = TaskScheduler()
