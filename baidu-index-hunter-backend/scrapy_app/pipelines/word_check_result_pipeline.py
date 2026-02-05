"""
关键词检查结果 Pipeline

将检查结果保存到 Redis，用于缓存和查询
不保存到 CSV 或数据库
"""
import json
import redis
from scrapy import signals


class WordCheckResultPipeline:
    """关键词检查结果 Pipeline - 保存到 Redis"""
    
    # Redis 键前缀
    REDIS_KEY_PREFIX = "baidu_index:word_check:"
    # 缓存过期时间（7天）
    REDIS_EXPIRE = 60 * 60 * 24 * 7
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.redis_client = None
        self.redis_config = crawler.settings.get('REDIS_CONFIG', {})
    
    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls(crawler)
        crawler.signals.connect(pipeline.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signal=signals.spider_closed)
        return pipeline
    
    @property
    def spider(self):
        """获取当前 spider 实例"""
        return self.crawler.spider
    
    def spider_opened(self, spider):
        """爬虫启动时初始化 Redis 连接"""
        # 只处理 word_check 爬虫
        if spider.name != 'word_check':
            return
        
        try:
            self.redis_client = redis.Redis(
                host=self.redis_config.get('host', 'localhost'),
                port=self.redis_config.get('port', 6379),
                db=self.redis_config.get('db', 0),
                password=self.redis_config.get('password'),
                decode_responses=True
            )
            spider.logger.info('WordCheckResultPipeline: Redis connected')
        except Exception as e:
            spider.logger.error(f'WordCheckResultPipeline: Failed to connect Redis: {e}')
    
    def spider_closed(self, spider):
        """爬虫关闭时清理"""
        if self.redis_client:
            self.redis_client.close()
    
    def process_item(self, item, spider):
        """处理 item，保存到 Redis"""
        # 只处理 word_check 爬虫
        if spider.name != 'word_check':
            return item
        
        try:
            keyword = item.get('keyword')
            task_id = item.get('task_id')
            exists = item.get('exists', False)
            error = item.get('error')
            
            if keyword and self.redis_client:
                # 保存关键词检查结果到 Redis
                result_data = {
                    'exists': exists,
                    'checked_at': item.get('crawl_time'),
                    'error': error
                }
                
                # 使用关键词作为键
                redis_key = f"{self.REDIS_KEY_PREFIX}{keyword}"
                self.redis_client.setex(
                    redis_key,
                    self.REDIS_EXPIRE,
                    json.dumps(result_data, ensure_ascii=False)
                )
                
                # 同时保存到任务结果集合中（用于 API 查询）
                if task_id:
                    task_result_key = f"baidu_index:word_check_task:{task_id}"
                    self.redis_client.hset(
                        task_result_key,
                        keyword,
                        json.dumps({'exists': exists, 'error': error}, ensure_ascii=False)
                    )
                    # 设置任务结果过期时间（1 小时）
                    self.redis_client.expire(task_result_key, 3600)
                
                spider.logger.debug(f"Saved word check result to Redis: {keyword} -> {exists}")
        
        except Exception as e:
            spider.logger.error(f"Failed to save word check result to Redis: {e}")
        
        return item
