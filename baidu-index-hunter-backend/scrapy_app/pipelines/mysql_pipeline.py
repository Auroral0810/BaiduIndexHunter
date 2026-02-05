"""
MySQL 统计管道

更新数据库中的统计信息
"""
import logging
from datetime import datetime


class MySQLStatsPipeline:
    """MySQL 统计管道"""
    
    def __init__(self, crawler, mysql_config):
        self.crawler = crawler
        self.logger = logging.getLogger(__name__)
        self.mysql_config = mysql_config
        self.mysql = None
        self.item_count = 0
        self.last_update_count = 0
        self.update_interval = 100  # 每处理 100 个 Item 更新一次进度
    
    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        return cls(
            crawler=crawler,
            mysql_config=settings.get('MYSQL_CONFIG', {}),
        )
    
    @property
    def spider(self):
        """获取当前 spider 实例"""
        return self.crawler.spider
    
    def open_spider(self):
        """爬虫启动时初始化数据库连接"""
        try:
            from db.mysql_manager import MySQLManager
            self.mysql = MySQLManager()
            self.logger.info('MySQL stats pipeline initialized')
        except Exception as e:
            self.logger.error(f'Failed to initialize MySQL: {e}')
    
    def close_spider(self):
        """爬虫关闭时更新最终统计数据"""
        try:
            self._update_final_statistics()
        except Exception as e:
            self.logger.error(f"Failed to update final statistics: {e}")
    
    def process_item(self, item):
        """统计处理的 Item 数量"""
        self.item_count += 1
        
        # 定期更新进度
        if self.item_count - self.last_update_count >= self.update_interval:
            self._update_task_progress()
            self.last_update_count = self.item_count
        
        return item
    
    def _update_task_progress(self):
        """更新任务进度"""
        if not self.mysql:
            return
        
        spider = self.spider
        task_id = getattr(spider, 'task_id', None)
        if not task_id:
            return
        
        try:
            total_items = getattr(spider, 'total_items', 0)
            completed_items = getattr(spider, 'completed_items', 0) + self.item_count
            failed_items = getattr(spider, 'failed_items', 0)
            
            progress = 0
            if total_items > 0:
                progress = min(100, round((completed_items / total_items) * 100, 2))
            
            update_query = """
                UPDATE spider_tasks 
                SET progress = %s, completed_items = %s, failed_items = %s, update_time = %s
                WHERE task_id = %s
            """
            self.mysql.execute_query(
                update_query, 
                (progress, completed_items, failed_items, datetime.now(), task_id)
            )
            
            self.logger.debug(f"Updated task progress: {progress}%")
            
        except Exception as e:
            self.logger.error(f"Failed to update task progress: {e}")
    
    def _update_final_statistics(self):
        """更新最终统计数据"""
        if not self.mysql:
            return
        
        spider = self.spider
        spider_name = spider.name
        
        try:
            stat_date = datetime.now().date()
            
            # 检查该日期是否已有统计记录
            check_query = """
                SELECT id, total_crawled_items FROM spider_statistics 
                WHERE stat_date = %s AND task_type = %s
            """
            stats = self.mysql.fetch_one(check_query, (stat_date, spider_name))
            
            if stats:
                # 更新现有记录
                current_total = stats.get('total_crawled_items', 0) or 0
                new_total = current_total + self.item_count
                
                update_query = """
                    UPDATE spider_statistics
                    SET total_crawled_items = %s,
                        update_time = %s
                    WHERE id = %s
                """
                self.mysql.execute_query(update_query, (new_total, datetime.now(), stats['id']))
                
                self.logger.info(f"Updated statistics: {current_total} -> {new_total}")
            else:
                # 创建新记录
                insert_query = """
                    INSERT INTO spider_statistics 
                    (stat_date, task_type, total_tasks, completed_tasks, failed_tasks, 
                     total_crawled_items, update_time) 
                    VALUES (%s, %s, 1, 1, 0, %s, %s)
                """
                self.mysql.execute_query(
                    insert_query, 
                    (stat_date, spider_name, self.item_count, datetime.now())
                )
                
                self.logger.info(f"Created new statistics record: {self.item_count} items")
                
        except Exception as e:
            self.logger.error(f"Failed to update statistics: {e}")
