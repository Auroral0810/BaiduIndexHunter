"""
Scrapy settings for BaiduIndexHunter project
百度指数爬虫 Scrapy 配置文件

配置统一由 core.config 管理
配置优先级：数据库 > 环境变量 > 默认值
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入统一配置管理器
from core.config import config, BAIDU_INDEX_API

# ==================== 基础配置 ====================
BOT_NAME = 'baidu_index_hunter'
SPIDER_MODULES = ['scrapy_app.spiders']
NEWSPIDER_MODULE = 'scrapy_app.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# ==================== 从统一配置读取 ====================
# 并发配置
CONCURRENT_REQUESTS = config.get('spider.max_workers', 16)
CONCURRENT_REQUESTS_PER_DOMAIN = config.get('spider.concurrent_per_domain', 8)
DOWNLOAD_DELAY = config.get('spider.default_interval', 0.3)
RANDOMIZE_DOWNLOAD_DELAY = True

# 超时配置
DOWNLOAD_TIMEOUT = config.get('spider.timeout', 30)

# 重试配置
RETRY_ENABLED = True
RETRY_TIMES = config.get('spider.retry_times', 3)
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 522, 524]

# ==================== Cookie 配置 ====================
COOKIES_ENABLED = False  # 使用自定义中间件

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
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None,
    
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
    'scrapy_app.pipelines.validation_pipeline.DataValidationPipeline': 100, # 100指的是优先级，数字越小优先级越高
    'scrapy_app.pipelines.word_check_result_pipeline.WordCheckResultPipeline': 150,  # 关键词检查结果保存到 Redis
    'scrapy_app.pipelines.csv_pipeline.CSVExportPipeline': 300,
    'scrapy_app.pipelines.mysql_pipeline.MySQLStatsPipeline': 400,
}

# ==================== 扩展配置 ====================
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,
    'scrapy_app.extensions.websocket_extension.WebSocketExtension': 100,
    'scrapy_app.extensions.checkpoint_extension.CheckpointExtension': 200,
    'scrapy_app.extensions.task_status_extension.TaskStatusExtension': 300,
}

# ==================== 断点续传配置 ====================
JOBDIR_BASE = str(PROJECT_ROOT / 'output' / 'scrapy_jobs')

# ==================== 日志配置 ====================
LOG_LEVEL = config.get('log.level', 'INFO')
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'
LOG_FILE = None

# ==================== 数据库配置（从统一配置读取） ====================
MYSQL_CONFIG = config.mysql_config
REDIS_CONFIG = config.redis_config

# ==================== Cookie 管理配置 ====================
COOKIE_CONFIG = {
    'block_cooldown': config.get('cookie.block_cooldown', 1800),
    'max_usage_per_day': config.get('cookie.max_usage_per_day', 1800),
    'rotation_strategy': config.get('cookie.rotation_strategy', 'round_robin'),
}

# ==================== 输出配置 ====================
OUTPUT_DIR = str(PROJECT_ROOT / 'output')
OUTPUT_CONFIG = {
    'default_format': config.get('output.default_format', 'csv'),
    'csv_encoding': config.get('output.csv_encoding', 'utf-8-sig'),
}

# 确保输出目录存在
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
Path(JOBDIR_BASE).mkdir(parents=True, exist_ok=True)

# ==================== 自定义配置 ====================
KEYWORDS_BATCH_SIZE = 5
PROGRESS_UPDATE_INTERVAL = 50
CHECKPOINT_SAVE_INTERVAL = 100

# ==================== 其他配置 ====================
CLEANUP_JOBDIR_ON_FINISH = True
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
FEED_EXPORT_ENCODING = 'utf-8'
