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

# 导入具体爬虫类 (用于直接调用或类型检查)
from src.engine.spider.search_index_crawler import search_index_crawler
from src.engine.spider.feed_index_crawler import feed_index_crawler
from src.engine.spider.word_graph_crawler import word_graph_crawler
from src.engine.spider.demographic_attributes_crawler import demographic_attributes_crawler
from src.engine.spider.interest_profile_crawler import interest_profile_crawler
from src.engine.spider.region_distribution_crawler import region_distribution_crawler


class TaskExecutor:
    """任务执行器，负责执行爬虫任务"""

    def __init__(self):
        """初始化任务执行器"""
        self.spider = BaiduIndexSpider()
        
        # 爬虫映射表：根据任务类型映射到具体的爬虫实例
        self.crawler_map = {
            'search_index': search_index_crawler,
            'feed_index': feed_index_crawler,
            'word_graph': word_graph_crawler,
            'demographic_attributes': demographic_attributes_crawler,
            'interest_profile': interest_profile_crawler,
            'region_distribution': region_distribution_crawler
        }

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
            # 1. 验证任务类型
            crawler = self.crawler_map.get(task_type)
            if not crawler:
                error_msg = f"未知的任务类型: {task_type}"
                log.error(error_msg)
                self._update_task_status(task_id, 'failed', error_message=error_msg)
                return

            # 2. 更新任务状态为运行中
            self._update_task_status(task_id, 'running')
            
            # 3. 准备执行参数
            # 大多数爬虫的 crawl 方法参数名基本一致，这里进行统一解包
            # 注意：BaseCrawler 定义的 crawl 方法签名可能会有细微差别，但大多兼容 **kwargs
            
            # 注入恢复参数
            if parameters.get('resume', False) or checkpoint_path:
                parameters['resume'] = True
                parameters['checkpoint_task_id'] = task_id  # 恢复时通常使用当前 task_id 查找检查点
            
            # 注入 task_id 以便爬虫内部使用
            parameters['task_id'] = task_id
            
            # 4. 执行爬取
            # 具体的 Crawler 负责：
            # - 创建输出目录
            # - 创建/加载检查点
            # - 更新数据库进度 (通过 BaseCrawler._update_task_db_status)
            # - 异常处理与重试
            # - 保存结果数据
            
            success = crawler.crawl(**parameters)
            
            # 5. 任务结束处理
            # 爬虫内部通常会更新状态，但为了保险起见，这里做最后的状态确认
            if success:
                log.info(f"任务执行成功: {task_id}")
                # 只有当爬虫没有明确更新为 completed 时，这里才更新
                # 通常 BaseCrawler 会在 _finalize_crawl 中处理
            else:
                log.warning(f"任务执行未完全成功: {task_id}")
                # 如果爬虫返回 False，可能已经在内部更新了 failed 状态，这里可以根据需要补充逻辑

        except Exception as e:
            error_msg = f"任务执行发生未捕获异常: {str(e)}"
            log.error(error_msg)
            log.error(traceback.format_exc())
            self._update_task_status(task_id, 'failed', error_message=error_msg)

    def stop_task(self, task_id: str):
        """
        停止任务
        :param task_id: 任务ID
        """
        log.info(f"正在请求停止任务: {task_id}")
        
        # 遍历所有爬虫，查找正在运行该 task_id 的爬虫并停止它
        # 注意：目前的单例模式下，如果不加锁或并发控制，可能会影响其他任务
        # 但鉴于目前的架构，我们尝试向所有爬虫发送停止信号（如果是它们正在运行的任务）
        
        stopped = False
        for name, crawler in self.crawler_map.items():
            # 假设爬虫实例有 current_task_id 属性或类似机制
            if getattr(crawler, 'task_id', None) == task_id:
                log.info(f"找到正在执行任务 {task_id} 的爬虫: {name}，发送停止信号")
                # BaseCrawler 通常通过信号处理停止，但在多线程下需要更优雅的方式
                # 这里暂时假设设置一个标志位
                crawler.is_running = False # 这是一个假设的标志位，需要在 BaseCrawler 中支持
                stopped = True
        
        if not stopped:
            log.warning(f"未找到正在执行任务 {task_id} 的爬虫实例")

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