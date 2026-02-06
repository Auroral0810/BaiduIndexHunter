"""
项目全局配置
"""
import os
import multiprocessing
from dotenv import load_dotenv
from pathlib import Path
from fake_useragent import UserAgent
ua = UserAgent()
useragent=ua.random#随机生成useragent

# 加载环境变量
env_path = Path(__file__).parent.parent.parent / 'config' / '.env'
load_dotenv(dotenv_path=env_path)

# 数据库配置
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', '123456'),
    'db': os.getenv('MYSQL_DB', 'BaiduIndexHunter'),
}

# Redis配置
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': int(os.getenv('REDIS_DB', 0)),
    'password': os.getenv('REDIS_PASSWORD', '') or None,
}

# 阿里云OSS配置
OSS_CONFIG = {
    'enabled': os.getenv('OSS_ENABLED', 'False').lower() == 'true',  # 是否启用OSS上传，默认False
    'url': os.getenv('OSS_URL'),
    'endpoint': os.getenv('OSS_ENDPOINT'),
    'access_key_id': os.getenv('OSS_ACCESS_KEY_ID'),
    'access_key_secret': os.getenv('OSS_ACCESS_KEY_SECRET'),
    'bucket_name': os.getenv('OSS_BUCKET_NAME'),
    'region': os.getenv('OSS_REGION'),
}

# API配置
API_CONFIG = {
    'host': os.getenv('API_HOST', '0.0.0.0'),
    'port': int(os.getenv('API_PORT', 5001)),
    'debug': os.getenv('API_DEBUG', 'True').lower() == 'true',
    'secret_key': os.getenv('API_SECRET_KEY', 'baidu_index_hunter_secret_key'),
    'token_expire': int(os.getenv('API_TOKEN_EXPIRE', 86400)),  # 默认1天
    'cors_origins': os.getenv('API_CORS_ORIGINS', '*').split(','),
}

# 任务配置
TASK_CONFIG = {
    'max_concurrent_tasks': int(os.getenv('MAX_CONCURRENT_TASKS', 10)),  # 最大并发任务数
    'task_queue_check_interval': int(os.getenv('TASK_QUEUE_CHECK_INTERVAL', 10)),  # 任务队列检查间隔（秒）
    'default_task_priority': int(os.getenv('DEFAULT_TASK_PRIORITY', 5)),  # 默认任务优先级（1-10）
    'max_retry_count': int(os.getenv('MAX_RETRY_COUNT', 3)),  # 任务最大重试次数
    'retry_delay': int(os.getenv('RETRY_DELAY', 300)),  # 任务重试延迟（秒）
}

# 登录和健康检查配置
LOGIN_INTERVAL = int(os.getenv('LOGIN_INTERVAL', 86400))  # 默认24小时
HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', 3600))  # 默认1小时

# 日志配置
LOG_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'retention': int(os.getenv('LOG_RETENTION', 7)),  # 日志保留天数
    'format': os.getenv('LOG_FORMAT', '%(asctime)s - %(levelname)s - %(name)s - %(message)s'),
    'file_size': int(os.getenv('LOG_FILE_SIZE', 10 * 1024 * 1024)),  # 单个日志文件大小限制，默认10MB
    'backup_count': int(os.getenv('LOG_BACKUP_COUNT', 5)),  # 日志文件备份数量
}

LOG_DIR = Path(__file__).parent.parent.parent / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Cookie相关配置
# 注意：百度指数Cookie不会过期，只会被锁住
COOKIE_CONFIG = {
    'min_available_count': int(os.getenv('COOKIE_MIN_AVAILABLE_COUNT', 10)),  # 最小可用Cookie数量
    'max_login_retry': int(os.getenv('COOKIE_MAX_LOGIN_RETRY', 2)),  # 登录重试最大次数
    'block_cooldown': int(os.getenv('COOKIE_BLOCK_COOLDOWN', 1800)),  # Cookie被锁后的冷却时间（秒），默认30分钟
    'expiration_buffer': int(os.getenv('COOKIE_EXPIRATION_BUFFER', 3600)),  # Cookie过期前的缓冲时间（秒），默认1小时
    'rotation_strategy': os.getenv('COOKIE_ROTATION_STRATEGY', 'round_robin'),  # Cookie轮换策略：round_robin, random, least_used
    'max_usage_per_day': int(os.getenv('COOKIE_MAX_USAGE_PER_DAY', 1800)),  # 每个Cookie每天最大使用次数
}

# 百度指数API配置
BAIDU_INDEX_API = {
    'search_url': 'https://index.baidu.com/api/SearchApi/index', #搜索指数的url
    'trend_url': 'https://index.baidu.com/api/FeedSearchApi/getFeedIndex', #资讯指数的url
    'word_graph_url': 'https://index.baidu.com/api/WordGraph/multi', #需求图谱的url
    'social_api_url': 'https://index.baidu.com/api/SocialApi/baseAttributes', #社会指数的url
    'region_api_url': 'https://index.baidu.com/api/SearchApi/region', #地域指数的url
    'interest_api_url': 'https://index.baidu.com/api/SocialApi/interest', #兴趣指数的url
    'user_agent': useragent,
    'referer': 'https://index.baidu.com/v2/main/index.html', # 构造cipher-text的url
}

# 爬虫配置
SPIDER_CONFIG = {
    'min_interval': float(os.getenv('SPIDER_MIN_INTERVAL', 0.3)),  # 请求间隔最小秒数，降低到0.1秒
    'max_interval': float(os.getenv('SPIDER_MAX_INTERVAL', 0.5)),  # 请求间隔最大秒数，降低到0.3秒
    'default_interval': float(os.getenv('SPIDER_DEFAULT_INTERVAL', 0.4)),  # 默认请求间隔秒数，降低到0.2秒
    'retry_times': int(os.getenv('SPIDER_RETRY_TIMES', 2)),  # 请求失败重试次数
    'timeout': int(os.getenv('SPIDER_TIMEOUT', 10)),     # 请求超时时间（秒），降低到10秒
    'max_workers': int(os.getenv('SPIDER_MAX_WORKERS', min(10, multiprocessing.cpu_count()*4))),  # 最大工作线程数，增加到20或CPU核心数的6倍
    'max_consecutive_failures': int(os.getenv('SPIDER_MAX_CONSECUTIVE_FAILURES', 2)),  # 最大连续失败次数
    'failure_multiplier': float(os.getenv('SPIDER_FAILURE_MULTIPLIER', 1.1)),  # 失败后等待时间倍数，降低到1.1
    'user_agent_rotation': os.getenv('SPIDER_USER_AGENT_ROTATION', 'True').lower() == 'true',  # 是否轮换User-Agent
    'proxy_enabled': os.getenv('SPIDER_PROXY_ENABLED', 'False').lower() == 'true',  # 是否启用代理
    'proxy_url': os.getenv('SPIDER_PROXY_URL', ''),  # 代理URL
    'proxy_auth': os.getenv('SPIDER_PROXY_AUTH', ''),  # 代理认证信息
}

# 输出配置
OUTPUT_CONFIG = {
    'default_format': os.getenv('OUTPUT_DEFAULT_FORMAT', 'csv'),  # 默认输出格式：csv, excel
    'csv_encoding': os.getenv('OUTPUT_CSV_ENCODING', 'utf-8-sig'),  # CSV文件编码
    'excel_sheet_name': os.getenv('OUTPUT_EXCEL_SHEET_NAME', 'BaiduIndex'),  # Excel工作表名称
    'file_name_template': os.getenv('OUTPUT_FILE_NAME_TEMPLATE', '{task_type}_{timestamp}'),  # 输出文件名模板
}

# Cipher-Text配置
CIPHER_TEXT_JS_PATH = Path(__file__).parent.parent / 'engine' / 'crypto' / 'Cipher-Text.js'

# 输出目录配置
OUTPUT_DIR = os.getenv('OUTPUT_DIR', str(Path(__file__).parent.parent.parent / 'output'))
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True) 