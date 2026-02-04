"""
任务状态扩展

管理任务状态的更新
"""
import logging
from datetime import datetime
from scrapy import signals


class TaskStatusExtension:
    """任务状态管理扩展"""
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.logger = logging.getLogger(__name__)
        self.mysql = None
    
    @classmethod
    def from_crawler(cls, crawler):
        ext = cls(crawler)
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.spider_idle, signal=signals.spider_idle)
        return ext
    
    def spider_opened(self, spider):
        """爬虫启动时更新任务状态为运行中"""
        try:
            from db.mysql_manager import MySQLManager
            self.mysql = MySQLManager()
        except Exception as e:
            self.logger.error(f'Failed to initialize MySQL: {e}')
            return
        
        task_id = getattr(spider, 'task_id', None)
        if not task_id:
            return
        
        try:
            now = datetime.now()
            
            # 更新任务状态为运行中
            update_query = """
                UPDATE spider_tasks 
                SET status = 'running', 
                    start_time = COALESCE(start_time, %s),
                    update_time = %s
                WHERE task_id = %s
            """
            self.mysql.execute_query(update_query, (now, now, task_id))
            
            # 更新 task_queue 状态
            queue_query = """
                UPDATE task_queue 
                SET status = 'processing', start_time = %s 
                WHERE task_id = %s AND start_time IS NULL
            """
            self.mysql.execute_query(queue_query, (now, task_id))
            
            self.logger.info(f"Task {task_id} status updated to running")
            
        except Exception as e:
            self.logger.error(f"Failed to update task status: {e}")
    
    def spider_closed(self, spider, reason):
        """爬虫关闭时更新任务状态"""
        task_id = getattr(spider, 'task_id', None)
        if not task_id or not self.mysql:
            return
        
        try:
            now = datetime.now()
            
            # 根据关闭原因确定状态
            if reason == 'finished':
                status = 'completed'
                error_message = None
            elif reason == 'shutdown':
                status = 'paused'
                error_message = '用户手动停止任务'
            elif reason == 'cancelled':
                status = 'cancelled'
                error_message = '任务被取消'
            elif reason == 'no_cookie_available':
                status = 'paused'
                error_message = '所有Cookie均被锁定，任务暂停等待可用Cookie'
            else:
                status = 'failed'
                error_message = f'任务执行失败: {reason}'
            
            # 计算进度
            total = getattr(spider, 'total_items', 0)
            completed = getattr(spider, 'completed_items', 0)
            failed = getattr(spider, 'failed_items', 0)
            progress = min(100, round((completed / total) * 100, 2)) if total > 0 else 0
            
            # 更新任务状态
            update_query = """
                UPDATE spider_tasks 
                SET status = %s, 
                    progress = %s,
                    completed_items = %s,
                    failed_items = %s,
                    error_message = %s,
                    update_time = %s,
                    end_time = %s
                WHERE task_id = %s
            """
            
            end_time = now if status in ['completed', 'failed', 'cancelled'] else None
            
            self.mysql.execute_query(
                update_query, 
                (status, progress, completed, failed, error_message, now, end_time, task_id)
            )
            
            # 更新 task_queue 状态
            queue_status = 'completed' if status == 'completed' else \
                          'failed' if status == 'failed' else \
                          'cancelled' if status == 'cancelled' else 'waiting'
            
            queue_query = """
                UPDATE task_queue 
                SET status = %s, complete_time = %s 
                WHERE task_id = %s
            """
            queue_time = now if status in ['completed', 'failed', 'cancelled'] else None
            self.mysql.execute_query(queue_query, (queue_status, queue_time, task_id))
            
            # 更新统计信息
            if status in ['completed', 'failed']:
                self._update_spider_statistics(spider, status)
            
            self.logger.info(f"Task {task_id} final status: {status}")
            
        except Exception as e:
            self.logger.error(f"Failed to update final task status: {e}")
    
    def spider_idle(self, spider):
        """爬虫空闲时"""
        # 可以在这里添加额外的逻辑
        pass
    
    def _update_spider_statistics(self, spider, status):
        """更新爬虫统计表"""
        if not self.mysql:
            return
        
        try:
            stat_date = datetime.now().date()
            task_type = spider.name
            
            # 检查是否存在统计记录
            check_query = """
                SELECT id, total_tasks, completed_tasks, failed_tasks
                FROM spider_statistics
                WHERE stat_date = %s AND task_type = %s
            """
            stats = self.mysql.fetch_one(check_query, (stat_date, task_type))
            
            if stats:
                # 更新现有记录
                update_query = """
                    UPDATE spider_statistics 
                    SET total_tasks = total_tasks + 1,
                        completed_tasks = completed_tasks + %s,
                        failed_tasks = failed_tasks + %s,
                        update_time = %s
                    WHERE id = %s
                """
                completed_inc = 1 if status == 'completed' else 0
                failed_inc = 1 if status == 'failed' else 0
                
                self.mysql.execute_query(
                    update_query, 
                    (completed_inc, failed_inc, datetime.now(), stats['id'])
                )
            else:
                # 创建新记录
                insert_query = """
                    INSERT INTO spider_statistics
                    (stat_date, task_type, total_tasks, completed_tasks, failed_tasks, update_time)
                    VALUES (%s, %s, 1, %s, %s, %s)
                """
                completed = 1 if status == 'completed' else 0
                failed = 1 if status == 'failed' else 0
                
                self.mysql.execute_query(
                    insert_query, 
                    (stat_date, task_type, completed, failed, datetime.now())
                )
                
        except Exception as e:
            self.logger.error(f"Failed to update spider statistics: {e}")
