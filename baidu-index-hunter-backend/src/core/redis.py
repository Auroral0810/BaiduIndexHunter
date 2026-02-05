"""
Redis 客户端模块
"""
import redis
from src.core.config import REDIS_CONFIG
from src.core.logger import log

class RedisClient:
    """Redis 客户端单例类"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance._client = None
            cls._instance._connect_redis()
        return cls._instance
    
    def _connect_redis(self):
        """连接 Redis"""
        try:
            self._client = redis.Redis(
                host=REDIS_CONFIG['host'],
                port=REDIS_CONFIG['port'],
                db=REDIS_CONFIG['db'],
                password=REDIS_CONFIG.get('password'),
                decode_responses=True  # 自动解码
            )
            # 测试连接
            self._client.ping()
            log.info("Redis 连接成功")
        except Exception as e:
            log.error(f"Redis 连接失败: {e}")
            self._client = None
    
    def get_client(self):
        """获取 Redis 客户端"""
        if self._client is None:
            self._connect_redis()
        return self._client

# 全局单例
redis_client = RedisClient().get_client()
