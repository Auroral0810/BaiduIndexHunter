"""
WebSocket 扩展

实时推送爬虫状态到前端
"""
import logging
from scrapy import signals


class WebSocketExtension:
    """WebSocket 状态推送扩展"""
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.logger = logging.getLogger(__name__)
        self.emit_func = None
        self.last_progress = -1
        self.update_interval = crawler.settings.getint('PROGRESS_UPDATE_INTERVAL', 50)
        self.item_count = 0
    
    @classmethod
    def from_crawler(cls, crawler):
        ext = cls(crawler)
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(ext.spider_error, signal=signals.spider_error)
        return ext
    
    def spider_opened(self, spider):
        """爬虫启动时初始化 WebSocket 并推送状态"""
        try:
            from utils.websocket_manager import emit_task_update
            self.emit_func = emit_task_update
            self.logger.info('WebSocket extension initialized')
        except ImportError:
            self.logger.warning('WebSocket manager not available')
            self.emit_func = None
        
        # 推送启动状态
        self._emit_update(spider, 'running', 0)
    
    def spider_closed(self, spider, reason):
        """爬虫关闭时推送最终状态"""
        if reason == 'finished':
            status = 'completed'
            progress = 100
        elif reason == 'shutdown' or reason == 'cancelled':
            status = 'paused'
            progress = self._calculate_progress(spider)
        elif reason == 'no_cookie_available':
            status = 'paused'
            progress = self._calculate_progress(spider)
        else:
            status = 'failed'
            progress = self._calculate_progress(spider)
        
        self._emit_update(spider, status, progress, reason=reason)
        self.logger.info(f"Spider closed with status: {status}, reason: {reason}")
    
    def item_scraped(self, item, response, spider):
        """每爬取指定数量的 Item 推送一次进度"""
        self.item_count += 1
        
        # 更新爬虫的已完成计数
        spider.completed_items = getattr(spider, 'completed_items', 0) + 1
        
        # 按间隔更新进度
        if self.item_count % self.update_interval == 0:
            progress = self._calculate_progress(spider)
            # 只有进度变化时才推送
            if progress != self.last_progress:
                self._emit_update(spider, 'running', progress)
                self.last_progress = progress
    
    def spider_error(self, failure, response, spider):
        """处理爬虫错误"""
        self.logger.error(f"Spider error: {failure}")
        # 增加失败计数
        spider.failed_items = getattr(spider, 'failed_items', 0) + 1
    
    def _emit_update(self, spider, status, progress, reason=None):
        """推送 WebSocket 更新"""
        if not self.emit_func:
            return
        
        task_id = getattr(spider, 'task_id', None)
        if not task_id:
            return
        
        try:
            update_data = {
                'progress': progress,
                'completed_items': getattr(spider, 'completed_items', 0),
                'failed_items': getattr(spider, 'failed_items', 0),
                'total_items': getattr(spider, 'total_items', 0),
                'status': status,
            }
            
            if reason:
                update_data['reason'] = reason
            
            self.emit_func(task_id, update_data)
            self.logger.debug(f"WebSocket update sent: {status}, progress: {progress}%")
            
        except Exception as e:
            self.logger.debug(f"WebSocket emit failed: {e}")
    
    def _calculate_progress(self, spider):
        """计算进度百分比"""
        total = getattr(spider, 'total_items', 0)
        completed = getattr(spider, 'completed_items', 0)
        
        if total <= 0:
            return 0
        
        return min(100, round((completed / total) * 100, 2))
