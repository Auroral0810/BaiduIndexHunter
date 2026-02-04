"""
Scrapy settings for BaiduIndexHunter project
百度指数爬虫 Scrapy 配置文件

集中管理所有爬虫配置，支持环境变量覆盖
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径，以便导入现有模块
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 加载环境变量
env_path = PROJECT_ROOT / '.env'
load_dotenv(dotenv_path=env_path)

# ==================== 基础配置 ====================
BOT_NAME = 'baidu_index_hunter'
SPIDER_MODULES = ['scrapy_app.spiders']
NEWSPIDER_MODULE = 'scrapy_app.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# ==================== 并发配置 ====================
# 全局并发请求数
CONCURRENT_REQUESTS = int(os.getenv('SPIDER_MAX_WORKERS', 16))
# 每个域名的并发请求数
CONCURRENT_REQUESTS_PER_DOMAIN = int(os.getenv('SPIDER_CONCURRENT_PER_DOMAIN', 8))
# 下载延迟（秒）
DOWNLOAD_DELAY = float(os.getenv('SPIDER_DEFAULT_INTERVAL', 0.3))
# 随机化下载延迟
RANDOMIZE_DOWNLOAD_DELAY = True

# ==================== 超时配置 ====================
DOWNLOAD_TIMEOUT = int(os.getenv('SPIDER_TIMEOUT', 30))

# ==================== 重试配置 ====================
RETRY_ENABLED = True
RETRY_TIMES = int(os.getenv('SPIDER_RETRY_TIMES', 3))
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 522, 524]

# ==================== Cookie 配置 ====================
# 禁用 Scrapy 内置 Cookie 管理，使用自定义中间件
COOKIES_ENABLED = False

# ==================== 请求头配置 ====================
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
}

# ==================== 中间件配置 ====================
DOWNLOADER_MIDDLEWARES = {
    # 禁用默认的 UserAgent 中间件
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    # 禁用默认的 Retry 中间件，使用自定义的
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    # 禁用默认的 Cookie 中间件
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None,
    
    # 自定义中间件
    'scrapy_app.middlewares.useragent_middleware.RandomUserAgentMiddleware': 400,
    'scrapy_app.middlewares.cookie_middleware.CookieRotationMiddleware': 543,
    'scrapy_app.middlewares.cipher_middleware.CipherTextMiddleware': 544,
    'scrapy_app.middlewares.retry_middleware.SmartRetryMiddleware': 550,
    'scrapy_app.middlewares.stats_middleware.RequestStatsMiddleware': 850,
}

SPIDER_MIDDLEWARES = {
    'scrapy_app.middlewares.spider_middleware.BaiduIndexSpiderMiddleware': 543,
}

# ==================== 数据管道配置 ====================
ITEM_PIPELINES = {
    'scrapy_app.pipelines.validation_pipeline.DataValidationPipeline': 100,
    'scrapy_app.pipelines.csv_pipeline.CSVExportPipeline': 300,
    'scrapy_app.pipelines.mysql_pipeline.MySQLStatsPipeline': 400,
}

# ==================== 扩展配置 ====================
EXTENSIONS = {
    # 禁用 Telnet 控制台
    'scrapy.extensions.telnet.TelnetConsole': None,
    # 自定义扩展
    'scrapy_app.extensions.websocket_extension.WebSocketExtension': 100,
    'scrapy_app.extensions.checkpoint_extension.CheckpointExtension': 200,
    'scrapy_app.extensions.task_status_extension.TaskStatusExtension': 300,
}

# ==================== 断点续传配置 ====================
# JobDir 目录，用于保存爬取状态实现断点续传
JOBDIR_BASE = os.path.join(str(PROJECT_ROOT), 'output', 'scrapy_jobs')

# ==================== 日志配置 ====================
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'
LOG_FILE = None  # 使用自定义日志处理

# ==================== 数据库配置 ====================
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'db': os.getenv('MYSQL_DB', 'BaiduIndexHunter'),
}

REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': int(os.getenv('REDIS_DB', 0)),
    'password': os.getenv('REDIS_PASSWORD', '') or None,
}

# ==================== 百度指数 API 配置 ====================
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

# ==================== Cookie 管理配置 ====================
COOKIE_CONFIG = {
    'block_cooldown': int(os.getenv('COOKIE_BLOCK_COOLDOWN', 1800)),
    'max_usage_per_day': int(os.getenv('COOKIE_MAX_USAGE_PER_DAY', 1800)),
    'rotation_strategy': os.getenv('COOKIE_ROTATION_STRATEGY', 'round_robin'),
}

# ==================== 输出配置 ====================
OUTPUT_DIR = os.getenv('OUTPUT_DIR', str(PROJECT_ROOT / 'output'))
OUTPUT_CONFIG = {
    'default_format': os.getenv('OUTPUT_DEFAULT_FORMAT', 'csv'),
    'csv_encoding': os.getenv('OUTPUT_CSV_ENCODING', 'utf-8-sig'),
}

# 确保输出目录存在
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
Path(JOBDIR_BASE).mkdir(parents=True, exist_ok=True)

# ==================== 自定义配置 ====================
# 每批处理的关键词数量
KEYWORDS_BATCH_SIZE = 5
# 进度更新间隔（每处理多少个 Item 更新一次）
PROGRESS_UPDATE_INTERVAL = 50
# 检查点保存间隔（每处理多少个请求保存一次）
CHECKPOINT_SAVE_INTERVAL = 100

# ==================== 其他配置 ====================
# 是否在完成后清理 JobDir
CLEANUP_JOBDIR_ON_FINISH = True
# 请求指纹算法
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
# Twisted 反应器
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
# Feed 导出编码
FEED_EXPORT_ENCODING = 'utf-8'
