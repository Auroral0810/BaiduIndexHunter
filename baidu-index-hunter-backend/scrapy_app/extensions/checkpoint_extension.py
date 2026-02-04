"""
检查点扩展

处理安全退出和断点续传
"""
import os
import signal
import logging
from scrapy import signals


class CheckpointExtension:
    """检查点扩展 - 处理安全退出和断点续传"""
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.logger = logging.getLogger(__name__)
        self.original_sigint = None
        self.original_sigterm = None
        self.is_shutting_down = False
    
    @classmethod
    def from_crawler(cls, crawler):
        ext = cls(crawler)
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.engine_started, signal=signals.engine_started)
        return ext
    
    def engine_started(self):
        """引擎启动时设置信号处理器"""
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        try:
            # 保存原有的信号处理器
            self.original_sigint = signal.getsignal(signal.SIGINT)
            self.original_sigterm = signal.getsignal(signal.SIGTERM)
            
            # 设置自定义信号处理器
            signal.signal(signal.SIGINT, self._handle_shutdown)
            signal.signal(signal.SIGTERM, self._handle_shutdown)
            
            self.logger.info('Signal handlers installed for graceful shutdown')
        except Exception as e:
            self.logger.warning(f'Failed to set signal handlers: {e}')
    
    def _handle_shutdown(self, signum, frame):
        """处理关闭信号"""
        if self.is_shutting_down:
            self.logger.warning('Force shutdown requested')
            # 调用原有的信号处理器进行强制退出
            if signum == signal.SIGINT and self.original_sigint:
                self.original_sigint(signum, frame)
            elif signum == signal.SIGTERM and self.original_sigterm:
                self.original_sigterm(signum, frame)
            return
        
        self.is_shutting_down = True
        self.logger.info("Received shutdown signal, stopping crawler gracefully...")
        self.logger.info("Scrapy will save state to JOBDIR for resumption")
        self.logger.info("Press Ctrl+C again to force quit")
        
        # 优雅关闭爬虫
        try:
            if self.crawler.engine.spider:
                self.crawler.engine.close_spider(
                    self.crawler.engine.spider, 
                    reason='shutdown'
                )
        except Exception as e:
            self.logger.error(f'Error during graceful shutdown: {e}')
    
    def spider_opened(self, spider):
        """爬虫启动时检查是否需要恢复"""
        task_id = getattr(spider, 'task_id', None)
        resume = getattr(spider, 'resume', False)
        
        if resume and task_id:
            self.logger.info(f"Resuming spider from checkpoint: {task_id}")
            self._log_jobdir_status(spider)
    
    def spider_closed(self, spider, reason):
        """爬虫关闭时保存检查点信息"""
        task_id = getattr(spider, 'task_id', None)
        
        self.logger.info(f"Spider closed with reason: {reason}")
        
        # Scrapy 会自动保存 JOBDIR 状态
        if reason in ['shutdown', 'cancelled']:
            self.logger.info("Checkpoint saved by Scrapy JobDir mechanism")
            self._update_task_checkpoint_path(spider)
        
        # 恢复原有的信号处理器
        try:
            if self.original_sigint:
                signal.signal(signal.SIGINT, self.original_sigint)
            if self.original_sigterm:
                signal.signal(signal.SIGTERM, self.original_sigterm)
        except Exception as e:
            self.logger.debug(f'Failed to restore signal handlers: {e}')
    
    def _log_jobdir_status(self, spider):
        """记录 JobDir 状态"""
        jobdir = self.crawler.settings.get('JOBDIR')
        if jobdir and os.path.exists(jobdir):
            files = os.listdir(jobdir)
            self.logger.info(f"JobDir contents: {files}")
        else:
            self.logger.info("No existing JobDir found, starting fresh")
    
    def _update_task_checkpoint_path(self, spider):
        """更新任务的检查点路径到数据库"""
        task_id = getattr(spider, 'task_id', None)
        if not task_id:
            return
        
        try:
            from db.mysql_manager import MySQLManager
            from datetime import datetime
            
            mysql = MySQLManager()
            jobdir = self.crawler.settings.get('JOBDIR')
            
            update_query = """
                UPDATE spider_tasks 
                SET checkpoint_path = %s, update_time = %s
                WHERE task_id = %s
            """
            mysql.execute_query(update_query, (jobdir, datetime.now(), task_id))
            
            self.logger.info(f"Updated checkpoint path: {jobdir}")
            
        except Exception as e:
            self.logger.error(f"Failed to update checkpoint path: {e}")
