"""
Scrapy 任务执行器

替换原有的 task_executor，使用 Scrapy 框架执行爬虫任务
"""
import os
import sys
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import log
from db.mysql_manager import MySQLManager


class ScrapyTaskExecutor:
    """Scrapy 任务执行器"""
    
    def __init__(self):
        self.mysql = MySQLManager()
        self.running_tasks = {}  # {task_id: is_running}
        self.scrapy_runner = None
        self._init_scrapy_runner()
    
    def _init_scrapy_runner(self):
        """初始化 Scrapy 运行器"""
        try:
            from scrapy_runner import scrapy_runner
            self.scrapy_runner = scrapy_runner
            log.info("Scrapy runner initialized")
        except ImportError as e:
            log.error(f"Failed to import scrapy_runner: {e}")
            raise
    
    def execute_task(self, task_id, task_type, parameters, checkpoint_path=None):
        """
        执行任务
        
        Args:
            task_id: 任务ID
            task_type: 任务类型
            parameters: 任务参数（字典或JSON字符串）
            checkpoint_path: 断点续传数据路径（已废弃，使用Scrapy JobDir）
            
        Returns:
            bool: 是否成功启动
        """
        log.info(f"Starting task {task_id}, type: {task_type}")
        
        # 标记任务为运行中
        self.running_tasks[task_id] = True
        
        try:
            # 解析参数
            if isinstance(parameters, str):
                parameters = json.loads(parameters)
            
            # 准备 Scrapy 参数
            spider_params = self._prepare_spider_params(task_type, parameters)
            
            # 检查是否为断点续传
            if parameters.get('resume', False):
                spider_params['resume'] = True
            
            # 更新任务状态为运行中
            self._update_task_status(task_id, 'running')
            
            # 启动 Scrapy 爬虫
            success = self.scrapy_runner.run_spider(
                task_id=task_id,
                task_type=task_type,
                parameters=spider_params,
                use_subprocess=True  # 使用子进程运行
            )
            
            if not success:
                self._update_task_status(task_id, 'failed', error_message="Failed to start spider")
                return False
            
            return True
            
        except Exception as e:
            log.error(f"Failed to execute task {task_id}: {e}")
            import traceback
            log.error(traceback.format_exc())
            self._update_task_status(task_id, 'failed', error_message=str(e))
            return False
        
        finally:
            # 注意：不在这里移除任务标记，因为爬虫可能还在运行
            pass
    
    def _prepare_spider_params(self, task_type, parameters):
        """准备 Scrapy 爬虫参数"""
        spider_params = {}
        
        # 通用参数
        if 'keywords' in parameters:
            keywords = parameters['keywords']
            if isinstance(keywords, list):
                spider_params['keywords'] = keywords
            else:
                spider_params['keywords'] = [keywords]
        
        # 城市参数
        if 'cities' in parameters:
            spider_params['cities'] = parameters['cities']
        
        # 时间参数
        if 'date_ranges' in parameters:
            spider_params['date_ranges'] = parameters['date_ranges']
        elif 'days' in parameters:
            spider_params['days'] = parameters['days']
        elif 'year_range' in parameters or 'yearRange' in parameters:
            year_range = parameters.get('year_range') or parameters.get('yearRange')
            spider_params['year_range'] = year_range
        
        # 特定任务类型的参数
        if task_type == 'word_graph':
            if 'datelists' in parameters:
                spider_params['datelists'] = parameters['datelists']
        
        if task_type == 'region_distribution':
            if 'regions' in parameters:
                spider_params['regions'] = parameters['regions']
        
        if task_type in ['demographic_attributes', 'interest_profile']:
            if 'batch_size' in parameters:
                spider_params['batch_size'] = parameters['batch_size']
        
        # 其他参数
        if 'batch_size' in parameters:
            spider_params['batch_size'] = parameters['batch_size']
        
        return spider_params
    
    def stop_task(self, task_id):
        """
        停止任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功停止
        """
        if self.scrapy_runner:
            success = self.scrapy_runner.stop_spider(task_id)
            if success:
                self.running_tasks[task_id] = False
                log.info(f"Task stopped: {task_id}")
            return success
        return False
    
    def is_task_running(self, task_id):
        """
        检查任务是否正在运行
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否正在运行
        """
        if self.scrapy_runner:
            return self.scrapy_runner.is_running(task_id)
        return task_id in self.running_tasks and self.running_tasks[task_id]
    
    def _update_task_status(self, task_id, status, progress=None, error_message=None):
        """更新任务状态"""
        try:
            update_data = {
                'status': status,
                'update_time': datetime.now(),
            }
            
            if progress is not None:
                update_data['progress'] = progress
            
            if error_message:
                update_data['error_message'] = error_message[:500]
            
            if status == 'running':
                # 检查是否已有开始时间
                check_query = "SELECT start_time FROM spider_tasks WHERE task_id = %s"
                result = self.mysql.fetch_one(check_query, (task_id,))
                if result and not result.get('start_time'):
                    update_data['start_time'] = datetime.now()
            
            if status in ['completed', 'failed', 'cancelled']:
                update_data['end_time'] = datetime.now()
            
            # 构建 SQL
            set_clause = ", ".join([f"{k} = %s" for k in update_data.keys()])
            values = list(update_data.values())
            values.append(task_id)
            
            query = f"UPDATE spider_tasks SET {set_clause} WHERE task_id = %s"
            self.mysql.execute_query(query, values)
            
            # 更新 task_queue
            if status in ['completed', 'failed', 'cancelled']:
                queue_query = """
                    UPDATE task_queue 
                    SET status = %s, complete_time = %s 
                    WHERE task_id = %s
                """
                queue_status = 'completed' if status == 'completed' else 'failed'
                self.mysql.execute_query(queue_query, (queue_status, datetime.now(), task_id))
            
        except Exception as e:
            log.error(f"Failed to update task status: {e}")


# 创建任务执行器实例
scrapy_task_executor = ScrapyTaskExecutor()
