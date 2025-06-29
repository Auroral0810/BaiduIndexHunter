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
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# 数据库配置
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', '123456'),
    'db': os.getenv('MYSQL_DB', 'cookie_pool'),
}

# Redis配置
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': int(os.getenv('REDIS_DB', 0)),
    'password': os.getenv('REDIS_PASSWORD', '') or None,
}

# 任务配置
LOGIN_INTERVAL = int(os.getenv('LOGIN_INTERVAL', 86400))  # 默认24小时
HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', 3600))  # 默认1小时

# 日志配置
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_RETENTION = int(os.getenv('LOG_RETENTION', 7))
LOG_DIR = Path(__file__).parent.parent / 'output/logs'
LOG_DIR.mkdir(exist_ok=True)

# Cookie相关配置
# 注意：百度指数Cookie不会过期，只会被锁住
COOKIE_MIN_AVAILABLE_COUNT = 3  # 最小可用Cookie数量，低于此值触发告警
MAX_LOGIN_RETRY = 2  # 登录重试最大次数
COOKIE_BLOCK_COOLDOWN = 1800  # Cookie被锁后的冷却时间（秒），默认30分钟
COOKIE_EXPIRATION_BUFFER = 3600  # Cookie过期前的缓冲时间（秒），默认1小时

# 百度指数API配置
BAIDU_INDEX_API = {
    'search_url': 'https://index.baidu.com/api/SearchApi/index', #搜索指数的url
    'trend_url': 'https://index.baidu.com/api/FeedSearchApi/getFeedIndex',
    'word_graph_url': 'https://index.baidu.com/api/WordGraph/multi',
    'social_api_url': 'https://index.baidu.com/api/SocialApi/baseAttributes',
    'region_api_url': 'https://index.baidu.com/api/SearchApi/region',
    'interest_api_url': 'https://index.baidu.com/api/SocialApi/interest',
    'user_agent': useragent,
    'referer': 'https://index.baidu.com/v2/main/index.html', # 构造cipher-text的url
}

# 爬虫配置
SPIDER_CONFIG = {
    'min_interval': 1.5,  # 请求间隔最小秒数
    'max_interval': 1.5,  # 请求间隔最大秒数
    'default_interval': 1.5,  # 默认请求间隔秒数
    'retry_times': 2,  # 请求失败重试次数
    'timeout': 15,     # 请求超时时间（秒）
    'max_workers': min(10, multiprocessing.cpu_count()*4),  # 最大工作线程数，增加到40个
    'max_consecutive_failures': 2,  # 最大连续失败次数
    'failure_multiplier': 1.2,  # 失败后等待时间倍数
}

# Cipher-Text配置
CIPHER_TEXT_JS_PATH = Path(__file__).parent.parent / 'utils' / 'Cipher-Text.js'

# 输出目录配置
OUTPUT_DIR = os.getenv('OUTPUT_DIR', str(Path(__file__).parent.parent / 'output'))
Path(OUTPUT_DIR).mkdir(exist_ok=True) 