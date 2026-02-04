"""
统一配置管理模块

配置优先级（从高到低）：
1. 数据库 system_config 表 - 运行时可修改的配置
2. 环境变量 .env 文件 - 敏感配置（密码、密钥）
3. 代码中的默认值 - 兜底默认值

使用方式：
    from core.config import config
    
    # 获取配置
    host = config.get('api.host')
    port = config.get('api.port', default=5001)
    
    # 获取分组配置
    spider_config = config.get_group('spider')
    
    # 设置配置（保存到数据库）
    config.set('spider.timeout', 30)
"""
import os
import sys
import json
import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dotenv import load_dotenv

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 加载环境变量
env_path = PROJECT_ROOT / '.env'
load_dotenv(dotenv_path=env_path)


class UnifiedConfig:
    """
    统一配置管理器
    
    整合环境变量、数据库配置和默认值，提供统一的配置访问接口
    """
    
    # ==================== 默认配置 ====================
    # 这些是硬编码的默认值，优先级最低
    DEFAULTS = {
        # 数据库配置（只从 .env 读取，不存数据库）
        'mysql.host': 'localhost',
        'mysql.port': 3306,
        'mysql.user': 'root',
        'mysql.password': '',
        'mysql.db': 'BaiduIndexHunter',
        
        # Redis 配置（只从 .env 读取）
        'redis.host': 'localhost',
        'redis.port': 6379,
        'redis.db': 0,
        'redis.password': '',
        
        # API 配置
        'api.host': '0.0.0.0',
        'api.port': 5001,
        'api.debug': False,
        'api.cors_origins': '*',
        'api.secret_key': 'baidu_index_hunter_secret_key',
        'api.token_expire': 86400,
        
        # 任务配置
        'task.max_concurrent_tasks': 10,
        'task.queue_check_interval': 10,
        'task.default_priority': 5,
        'task.max_retry_count': 3,
        'task.retry_delay': 300,
        
        # 爬虫配置
        'spider.min_interval': 0.3,
        'spider.max_interval': 0.5,
        'spider.default_interval': 0.3,
        'spider.retry_times': 3,
        'spider.timeout': 30,
        'spider.max_workers': 16,
        'spider.concurrent_per_domain': 8,
        'spider.user_agent_rotation': True,
        'spider.proxy_enabled': False,
        'spider.proxy_url': '',
        'spider.failure_multiplier': 1.1,
        
        # Cookie 配置
        'cookie.min_available_count': 5,
        'cookie.block_cooldown': 1800,
        'cookie.rotation_strategy': 'round_robin',
        'cookie.max_usage_per_day': 1800,
        
        # 输出配置
        'output.default_format': 'csv',
        'output.csv_encoding': 'utf-8-sig',
        'output.excel_sheet_name': 'BaiduIndex',
        'output.file_name_template': '{task_type}_{timestamp}',
        'output.use_oss': False,
        
        # OSS 配置（只从 .env 读取）
        'oss.url': '',
        'oss.endpoint': '',
        'oss.access_key_id': '',
        'oss.access_key_secret': '',
        'oss.bucket_name': '',
        'oss.region': '',
        
        # 日志配置
        'log.level': 'INFO',
        'log.retention': 7,
        'log.file_size': 10485760,
        'log.backup_count': 5,
        
        # UI 配置
        'ui.theme': 'light',
        'ui.language': 'zh_CN',
        'ui.items_per_page': 20,
        'ui.auto_refresh': True,
        'ui.refresh_interval': 30,
        
        # 系统配置
        'system.version': '2.0.0',
        'system.name': '百度指数爬虫',
        'system.maintenance_mode': False,
    }
    
    # 环境变量映射：config_key -> ENV_VAR_NAME
    ENV_MAPPING = {
        'mysql.host': 'MYSQL_HOST',
        'mysql.port': 'MYSQL_PORT',
        'mysql.user': 'MYSQL_USER',
        'mysql.password': 'MYSQL_PASSWORD',
        'mysql.db': 'MYSQL_DB',
        'redis.host': 'REDIS_HOST',
        'redis.port': 'REDIS_PORT',
        'redis.db': 'REDIS_DB',
        'redis.password': 'REDIS_PASSWORD',
        'api.host': 'API_HOST',
        'api.port': 'API_PORT',
        'api.debug': 'API_DEBUG',
        'api.secret_key': 'API_SECRET_KEY',
        'spider.max_workers': 'SPIDER_MAX_WORKERS',
        'spider.default_interval': 'SPIDER_DEFAULT_INTERVAL',
        'spider.timeout': 'SPIDER_TIMEOUT',
        'spider.retry_times': 'SPIDER_RETRY_TIMES',
        'log.level': 'LOG_LEVEL',
        'oss.url': 'OSS_URL',
        'oss.endpoint': 'OSS_ENDPOINT',
        'oss.access_key_id': 'OSS_ACCESS_KEY_ID',
        'oss.access_key_secret': 'OSS_ACCESS_KEY_SECRET',
        'oss.bucket_name': 'OSS_BUCKET_NAME',
        'oss.region': 'OSS_REGION',
    }
    
    # 只从环境变量读取的配置（敏感信息，不存数据库）
    ENV_ONLY_KEYS = {
        'mysql.host', 'mysql.port', 'mysql.user', 'mysql.password', 'mysql.db',
        'redis.host', 'redis.port', 'redis.db', 'redis.password',
        'oss.access_key_id', 'oss.access_key_secret',
        'api.secret_key',
    }
    
    def __init__(self):
        self._db_cache: Dict[str, Any] = {}
        self._cache_time: float = 0
        self._cache_ttl: int = 300  # 缓存有效期 5 分钟
        self._lock = threading.Lock()
        self._db_initialized = False
        self._mysql = None
    
    def _get_mysql_config(self) -> Dict[str, Any]:
        """获取 MySQL 配置（只从环境变量和默认值）"""
        return {
            'host': os.getenv('MYSQL_HOST', self.DEFAULTS['mysql.host']),
            'port': int(os.getenv('MYSQL_PORT', self.DEFAULTS['mysql.port'])),
            'user': os.getenv('MYSQL_USER', self.DEFAULTS['mysql.user']),
            'password': os.getenv('MYSQL_PASSWORD', self.DEFAULTS['mysql.password']),
            'db': os.getenv('MYSQL_DB', self.DEFAULTS['mysql.db']),
        }
    
    def _init_db(self):
        """延迟初始化数据库连接"""
        if self._db_initialized:
            return
        
        try:
            from db.mysql_manager import MySQLManager
            self._mysql = MySQLManager()
            self._db_initialized = True
            self._refresh_db_cache()
        except Exception as e:
            # 数据库连接失败时，仍然可以使用环境变量和默认值
            print(f"[Config] Database connection failed, using env/defaults: {e}")
            self._db_initialized = True  # 标记为已初始化，避免重复尝试
    
    def _refresh_db_cache(self):
        """刷新数据库配置缓存"""
        if not self._mysql:
            return
        
        try:
            query = "SELECT config_key, config_value FROM system_config"
            results = self._mysql.fetch_all(query)
            
            if results:
                with self._lock:
                    self._db_cache = {}
                    for row in results:
                        key = row['config_key']
                        value = self._parse_value(row['config_value'])
                        self._db_cache[key] = value
                    self._cache_time = time.time()
        except Exception as e:
            print(f"[Config] Failed to refresh db cache: {e}")
    
    def _parse_value(self, value: str) -> Any:
        """解析配置值，自动转换类型"""
        if value is None:
            return None
        
        # 尝试解析为 JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            pass
        
        # 布尔值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 整数
        try:
            return int(value)
        except ValueError:
            pass
        
        # 浮点数
        try:
            return float(value)
        except ValueError:
            pass
        
        return value
    
    def _convert_type(self, value: Any, target_type: type) -> Any:
        """转换值类型"""
        if value is None:
            return None
        
        if target_type == bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes')
            return bool(value)
        
        if target_type == int:
            return int(value)
        
        if target_type == float:
            return float(value)
        
        return value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        优先级：数据库 > 环境变量 > 默认值 > 传入的default
        
        Args:
            key: 配置键，如 'spider.timeout'
            default: 如果所有来源都没有该配置，返回此值
        
        Returns:
            配置值
        """
        # 延迟初始化数据库
        if not self._db_initialized:
            self._init_db()
        
        # 获取默认值的类型，用于类型转换
        default_value = self.DEFAULTS.get(key, default)
        target_type = type(default_value) if default_value is not None else str
        
        # 1. 对于敏感配置，只从环境变量读取
        if key in self.ENV_ONLY_KEYS:
            env_var = self.ENV_MAPPING.get(key)
            if env_var:
                env_value = os.getenv(env_var)
                if env_value is not None:
                    return self._convert_type(env_value, target_type)
            return default_value
        
        # 2. 检查缓存是否过期
        if time.time() - self._cache_time > self._cache_ttl:
            self._refresh_db_cache()
        
        # 3. 优先从数据库读取
        with self._lock:
            if key in self._db_cache:
                return self._db_cache[key]
        
        # 4. 从环境变量读取
        env_var = self.ENV_MAPPING.get(key)
        if env_var:
            env_value = os.getenv(env_var)
            if env_value is not None:
                return self._convert_type(env_value, target_type)
        
        # 5. 返回默认值
        return default_value
    
    def set(self, key: str, value: Any, description: str = None) -> bool:
        """
        设置配置值（保存到数据库）
        
        Args:
            key: 配置键
            value: 配置值
            description: 配置描述
        
        Returns:
            是否成功
        """
        # 敏感配置不保存到数据库
        if key in self.ENV_ONLY_KEYS:
            print(f"[Config] Cannot save sensitive config to database: {key}")
            return False
        
        if not self._db_initialized:
            self._init_db()
        
        if not self._mysql:
            return False
        
        try:
            # 转换为字符串
            if isinstance(value, bool):
                value_str = 'true' if value else 'false'
            elif isinstance(value, (dict, list)):
                value_str = json.dumps(value, ensure_ascii=False)
            else:
                value_str = str(value)
            
            # 更新或插入
            if description:
                query = """
                    INSERT INTO system_config (config_key, config_value, description) 
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE config_value = %s, description = %s, update_time = NOW()
                """
                self._mysql.execute_query(query, (key, value_str, description, value_str, description))
            else:
                query = """
                    INSERT INTO system_config (config_key, config_value) 
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE config_value = %s, update_time = NOW()
                """
                self._mysql.execute_query(query, (key, value_str, value_str))
            
            # 更新缓存
            with self._lock:
                self._db_cache[key] = value
            
            return True
        except Exception as e:
            print(f"[Config] Failed to set config: {key} - {e}")
            return False
    
    def get_group(self, prefix: str) -> Dict[str, Any]:
        """
        获取指定前缀的所有配置
        
        Args:
            prefix: 配置前缀，如 'spider'
        
        Returns:
            配置字典，键不包含前缀
        """
        if not self._db_initialized:
            self._init_db()
        
        result = {}
        prefix_dot = f"{prefix}."
        
        # 从默认值获取
        for key, value in self.DEFAULTS.items():
            if key.startswith(prefix_dot):
                short_key = key[len(prefix_dot):]
                result[short_key] = value
        
        # 从环境变量覆盖
        for key in result.keys():
            full_key = f"{prefix}.{key}"
            env_var = self.ENV_MAPPING.get(full_key)
            if env_var:
                env_value = os.getenv(env_var)
                if env_value is not None:
                    result[key] = self._parse_value(env_value)
        
        # 从数据库覆盖（优先级最高）
        with self._lock:
            for key, value in self._db_cache.items():
                if key.startswith(prefix_dot):
                    short_key = key[len(prefix_dot):]
                    result[short_key] = value
        
        return result
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        if not self._db_initialized:
            self._init_db()
        
        result = {}
        
        # 从默认值开始
        result.update(self.DEFAULTS)
        
        # 环境变量覆盖
        for config_key, env_var in self.ENV_MAPPING.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                result[config_key] = self._parse_value(env_value)
        
        # 数据库覆盖
        with self._lock:
            for key, value in self._db_cache.items():
                if key not in self.ENV_ONLY_KEYS:
                    result[key] = value
        
        return result
    
    def refresh(self):
        """强制刷新缓存"""
        self._refresh_db_cache()
    
    # ==================== 便捷访问属性 ====================
    
    @property
    def mysql_config(self) -> Dict[str, Any]:
        """MySQL 配置"""
        return self._get_mysql_config()
    
    @property
    def redis_config(self) -> Dict[str, Any]:
        """Redis 配置"""
        return {
            'host': self.get('redis.host'),
            'port': self.get('redis.port'),
            'db': self.get('redis.db'),
            'password': self.get('redis.password') or None,
        }
    
    @property
    def spider_config(self) -> Dict[str, Any]:
        """爬虫配置"""
        return self.get_group('spider')
    
    @property
    def cookie_config(self) -> Dict[str, Any]:
        """Cookie 配置"""
        return self.get_group('cookie')
    
    @property
    def output_config(self) -> Dict[str, Any]:
        """输出配置"""
        return self.get_group('output')
    
    @property
    def task_config(self) -> Dict[str, Any]:
        """任务配置"""
        return self.get_group('task')


# 创建全局配置实例
config = UnifiedConfig()


# ==================== 兼容性导出 ====================
# 为了兼容旧代码，提供字典形式的配置

def get_mysql_config() -> Dict[str, Any]:
    """获取 MySQL 配置（兼容旧代码）"""
    return config.mysql_config

def get_redis_config() -> Dict[str, Any]:
    """获取 Redis 配置（兼容旧代码）"""
    return config.redis_config

def get_spider_config() -> Dict[str, Any]:
    """获取爬虫配置（兼容旧代码）"""
    return config.spider_config

def get_task_config() -> Dict[str, Any]:
    """获取任务配置（兼容旧代码）"""
    return config.task_config

def get_cookie_config() -> Dict[str, Any]:
    """获取 Cookie 配置（兼容旧代码）"""
    return config.cookie_config


# ==================== 百度指数 API 配置 ====================
# 这些是固定的 API 地址，不需要配置
BAIDU_INDEX_API = {
    'search_url': 'https://index.baidu.com/api/SearchApi/index',
    'feed_url': 'https://index.baidu.com/api/FeedSearchApi/getFeedIndex',
    'word_graph_url': 'https://index.baidu.com/api/WordGraph/multi',
    'social_url': 'https://index.baidu.com/api/SocialApi/baseAttributes',
    'region_url': 'https://index.baidu.com/api/SearchApi/region',
    'interest_url': 'https://index.baidu.com/api/SocialApi/interest',
    'ptbk_url': 'https://index.baidu.com/Interface/ptbk',
    'referer': 'https://index.baidu.com/v2/main/index.html',
}


# ==================== 路径配置 ====================
OUTPUT_DIR = config.get('output.dir', str(PROJECT_ROOT / 'output'))
LOG_DIR = str(PROJECT_ROOT / 'output' / 'logs')
CIPHER_TEXT_JS_PATH = str(PROJECT_ROOT / 'utils' / 'Cipher-Text.js')

# 确保目录存在
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
