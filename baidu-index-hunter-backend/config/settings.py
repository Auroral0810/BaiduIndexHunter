"""
项目全局配置

此模块为兼容层，实际配置统一由 core.config 管理

配置优先级：数据库 > 环境变量 > 默认值
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入统一配置管理器
from core.config import (
    config,
    get_mysql_config,
    get_redis_config,
    get_spider_config,
    get_task_config,
    get_cookie_config,
    BAIDU_INDEX_API,
    OUTPUT_DIR,
    LOG_DIR,
    CIPHER_TEXT_JS_PATH,
)

# ==================== 兼容旧代码的配置导出 ====================

# 数据库配置
MYSQL_CONFIG = config.mysql_config

# Redis 配置
REDIS_CONFIG = config.redis_config

# API 配置
API_CONFIG = {
    'host': config.get('api.host'),
    'port': config.get('api.port'),
    'debug': config.get('api.debug'),
    'secret_key': config.get('api.secret_key'),
    'token_expire': config.get('api.token_expire'),
    'cors_origins': config.get('api.cors_origins', '*').split(',') if isinstance(config.get('api.cors_origins'), str) else ['*'],
}

# 任务配置
TASK_CONFIG = {
    'max_concurrent_tasks': config.get('task.max_concurrent_tasks'),
    'task_queue_check_interval': config.get('task.queue_check_interval'),
    'default_task_priority': config.get('task.default_priority'),
    'max_retry_count': config.get('task.max_retry_count'),
    'retry_delay': config.get('task.retry_delay'),
}

# Cookie 配置
COOKIE_CONFIG = {
    'min_available_count': config.get('cookie.min_available_count'),
    'block_cooldown': config.get('cookie.block_cooldown'),
    'rotation_strategy': config.get('cookie.rotation_strategy'),
    'max_usage_per_day': config.get('cookie.max_usage_per_day'),
    'max_login_retry': 2,
    'expiration_buffer': 3600,
}

# 爬虫配置
SPIDER_CONFIG = {
    'min_interval': config.get('spider.min_interval'),
    'max_interval': config.get('spider.max_interval'),
    'default_interval': config.get('spider.default_interval'),
    'retry_times': config.get('spider.retry_times'),
    'timeout': config.get('spider.timeout'),
    'max_workers': config.get('spider.max_workers'),
    'max_consecutive_failures': 2,
    'failure_multiplier': config.get('spider.failure_multiplier'),
    'user_agent_rotation': config.get('spider.user_agent_rotation'),
    'proxy_enabled': config.get('spider.proxy_enabled'),
    'proxy_url': config.get('spider.proxy_url'),
    'proxy_auth': '',
}

# 输出配置
OUTPUT_CONFIG = {
    'default_format': config.get('output.default_format'),
    'csv_encoding': config.get('output.csv_encoding'),
    'excel_sheet_name': config.get('output.excel_sheet_name'),
    'file_name_template': config.get('output.file_name_template'),
}

# 日志配置
LOG_CONFIG = {
    'level': config.get('log.level'),
    'retention': config.get('log.retention'),
    'format': '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    'file_size': config.get('log.file_size'),
    'backup_count': config.get('log.backup_count'),
}

# OSS 配置
OSS_CONFIG = {
    'enabled': config.get('output.use_oss', False),
    'url': config.get('oss.url'),
    'endpoint': config.get('oss.endpoint'),
    'access_key_id': config.get('oss.access_key_id'),
    'access_key_secret': config.get('oss.access_key_secret'),
    'bucket_name': config.get('oss.bucket_name'),
    'region': config.get('oss.region'),
}

# 登录和健康检查配置
LOGIN_INTERVAL = 86400
HEALTH_CHECK_INTERVAL = 3600

# 确保日志目录存在
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

# User-Agent（动态生成）
try:
    from fake_useragent import UserAgent
    ua = UserAgent()
    BAIDU_INDEX_API['user_agent'] = ua.random
except:
    BAIDU_INDEX_API['user_agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
