"""
任务执行器模块
负责具体任务的执行，协调各个爬虫模块
"""
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

from src.core.logger import log
from src.data.repositories.task_repository import task_repo
from src.engine.spider.baidu_index_spider import BaiduIndexSpider

# 导入具体爬虫类
from src.engine.spider.search_index_crawler import SearchIndexCrawler
from src.engine.spider.feed_index_crawler import FeedIndexCrawler
from src.engine.spider.word_graph_crawler import WordGraphCrawler
from src.engine.spider.demographic_attributes_crawler import DemographicAttributesCrawler
from src.engine.spider.interest_profile_crawler import InterestProfileCrawler
from src.engine.spider.region_distribution_crawler import RegionDistributionCrawler


class TaskExecutor:
    """任务执行器，负责执行爬虫任务"""

    def __init__(self):
        """初始化任务执行器"""
        self.spider = BaiduIndexSpider()
        
        # 爬虫类映射表：根据任务类型映射到具体的爬虫类
        self.crawler_classes = {
            'search_index': SearchIndexCrawler,
            'feed_index': FeedIndexCrawler,
            'word_graph': WordGraphCrawler,
            'demographic_attributes': DemographicAttributesCrawler,
            'interest_profile': InterestProfileCrawler,
            'region_distribution': RegionDistributionCrawler
        }
        
        # 正在运行的爬虫实例映射表: task_id -> crawler instance
        self.active_crawlers: Dict[str, Any] = {}

    def execute_task(self, task_id: str, task_type: str, parameters: Dict[str, Any], checkpoint_path: Optional[str] = None):
        """
        执行任务
        :param task_id: 任务ID
        :param task_type: 任务类型
        :param parameters: 任务参数
        :param checkpoint_path: 检查点路径 (可选)
        """
        log.info(f"开始执行任务: {task_id}, 类型: {task_type}")
        
        try:
            # 1. 获取爬虫类并实例化 (确保每个任务有独立实例)
            crawler_class = self.crawler_classes.get(task_type)
            if not crawler_class:
                error_msg = f"未知的任务类型: {task_type}"
                log.error(error_msg)
                self._update_task_status(task_id, 'failed', error_message=error_msg)
                return

            crawler = crawler_class()
            self.active_crawlers[task_id] = crawler
            
            # 2. 更新任务状态为运行中
            self._update_task_status(task_id, 'running')
            
            # 3. 准备执行参数
            # 注入恢复参数
            if parameters.get('resume', False) or checkpoint_path:
                parameters['resume'] = True
                parameters['checkpoint_task_id'] = task_id
            
            parameters['task_id'] = task_id
            
            # 4. 执行爬取
            try:
                success = crawler.crawl(**parameters)
                
                if success:
                    log.info(f"任务执行成功: {task_id}")
                else:
                    log.warning(f"任务执行结束(未成功): {task_id}")
            finally:
                # 任务结束，从活跃映射中移除
                if task_id in self.active_crawlers:
                    del self.active_crawlers[task_id]

        except Exception as e:
            error_msg = f"任务执行发生未捕获异常: {str(e)}"
            log.error(error_msg)
            log.error(traceback.format_exc())
            self._update_task_status(task_id, 'failed', error_message=error_msg)
            if task_id in self.active_crawlers:
                del self.active_crawlers[task_id]

    def stop_task(self, task_id: str):
        """
        停止任务
        :param task_id: 任务ID
        """
        log.info(f"正在请求停止任务: {task_id}")
        
        crawler = self.active_crawlers.get(task_id)
        if crawler:
            log.info(f"找到正在执行的任务 {task_id}，发送停止信号")
            crawler.is_running = False
            return True
        
        log.warning(f"未找到正在执行任务 {task_id} 的活跃爬虫实例")
        return False

    def _update_task_status(self, task_id: str, status: str, error_message: str = None):
        """
        更新任务状态 (辅助方法)
        :param task_id: 任务ID
        :param status: 状态
        :param error_message: 错误信息
        """
        try:
            task_repo.update_task_progress(
                task_id=task_id,
                status=status,
                error_message=error_message
            )
        except Exception as e:
            log.error(f"更新任务状态失败: {e}")

# 全局任务执行器实例
task_executor = TaskExecutor()