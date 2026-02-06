"""
统一日志系统解决方案
"""
import sys
import os
import logging
from pathlib import Path
from loguru import logger
from src.core.config import LOG_CONFIG, LOG_DIR
from collections import deque
import subprocess
from flask import Flask, request, g
import time
from datetime import datetime

class LoggerWithCache:
    """带有消息缓存的日志器"""
    
    def __init__(self, base_logger, console_max_logs=3000):
        self._logger = base_logger
        self._message_cache = deque(maxlen=500)
        self._console_log_count = 0
        self._console_max_logs = console_max_logs
    
    def _check_and_clear_console(self):
        """检查并在必要时清空控制台"""
        self._console_log_count += 1
        if self._console_log_count >= self._console_max_logs:
            try:
                subprocess.run(['clear'], check=True)
            except:
                print('\033[2J\033[1;1H', end='')
                sys.stdout.flush()
            self._console_log_count = 0
    
    def info(self, message, *args, **kwargs):
        self._message_cache.append(("INFO", message))
        self._check_and_clear_console()
        return self._logger.info(message, *args, **kwargs)
    
    def debug(self, message, *args, **kwargs):
        self._message_cache.append(("DEBUG", message))
        self._check_and_clear_console()
        return self._logger.debug(message, *args, **kwargs)
    
    def warning(self, message, *args, **kwargs):
        self._message_cache.append(("WARNING", message))
        self._check_and_clear_console()
        return self._logger.warning(message, *args, **kwargs)
    
    def error(self, message, *args, **kwargs):
        self._message_cache.append(("ERROR", message))
        self._check_and_clear_console()
        return self._logger.error(message, *args, **kwargs)
    
    def critical(self, message, *args, **kwargs):
        self._message_cache.append(("CRITICAL", message))
        self._check_and_clear_console()
        return self._logger.critical(message, *args, **kwargs)
    
    def last_message(self, level=None):
        """获取最近的日志消息"""
        if not self._message_cache:
            return ""
            
        if level:
            for msg_level, message in reversed(self._message_cache):
                if msg_level == level.upper():
                    return message
            return ""
        else:
            return self._message_cache[-1][1]
    
    def last_error_message(self):
        """获取最近的错误消息"""
        return self.last_message(level="ERROR")
    
    def __getattr__(self, name):
        return getattr(self._logger, name)


class InterceptHandler(logging.Handler):
    """
    拦截标准库日志并重定向到loguru
    """
    def emit(self, record):
        # 获取对应的loguru级别
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 查找调用者
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_unified_logger(console_max_logs=3000):
    """
    配置统一的日志系统
    """
    # 从配置中获取日志级别和保留天数
    log_level = LOG_CONFIG.get('level', 'INFO')
    log_retention = LOG_CONFIG.get('retention', 7)
    
    # 清除loguru默认处理程序
    logger.remove()
    
    # 添加控制台输出（统一格式）
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )
    
    # 添加文件输出（统一格式）
    log_file = LOG_DIR / "baidu_index_hunter_{time:YYYY-MM-DD}.log"
    logger.add(
        log_file,
        rotation="00:00",
        retention=log_retention,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        encoding="utf-8",
    )

    # 添加实时流输出 (WebSocket)
    logger.add(
        streaming_sink,
        level=log_level,
    )
    
    # 拦截标准库日志
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # 禁用特定的日志记录器以减少噪音
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    return LoggerWithCache(logger, console_max_logs)


_log_pusher = None

def set_log_pusher(pusher_func):
    """设置日志推送器"""
    global _log_pusher
    _log_pusher = pusher_func

def streaming_sink(message):
    """实时日志推送到 WebSocket"""
    if _log_pusher:
        try:
            record = message.record
            _log_pusher({
                "time": record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                "level": record["level"].name,
                "name": record["name"],
                "function": record["function"],
                "line": record["line"],
                "message": record["message"]
            })
        except:
            pass

def setup_unified_logger(console_max_logs=3000):
    """
    配置统一的日志系统
    """
    # 从配置中获取日志级别和保留天数
    log_level = LOG_CONFIG.get('level', 'INFO')
    log_retention = LOG_CONFIG.get('retention', 7)
    
    # 清除loguru默认处理程序
    logger.remove()
    
    # 添加控制台输出（统一格式）
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )
    
    # 添加文件输出（统一格式）
    log_file = LOG_DIR / "baidu_index_hunter_{time:YYYY-MM-DD}.log"
    logger.add(
        log_file,
        rotation="00:00",
        retention=log_retention,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        encoding="utf-8",
    )

    # 添加实时流输出 (WebSocket)
    logger.add(
        streaming_sink,
        level=log_level,
    )
    
    # 拦截标准库日志
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # 禁用特定的日志记录器以减少噪音
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    return LoggerWithCache(logger, console_max_logs)


def setup_flask_request_logging(app: Flask, log_instance):
    """
    设置Flask请求日志中间件
    """
    
    @app.before_request
    def log_request_info():
        """记录请求开始"""
        g.start_time = time.time()
        
        # 跳过健康检查和静态资源的日志
        if request.path in ['/api/health', '/favicon.ico'] or request.path.startswith('/static/'):
            return
            
        # 记录请求信息
        log_instance.info(
            f"Request started: {request.method} {request.path} "
            f"from {request.remote_addr} "
            f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
        )
    
    @app.after_request
    def log_request_result(response):
        """记录请求结果"""
        # 跳过健康检查和静态资源的日志
        if request.path in ['/api/health', '/favicon.ico'] or request.path.startswith('/static/'):
            return response
            
        # 计算请求耗时
        duration = time.time() - g.get('start_time', time.time())
        
        # 根据状态码选择日志级别
        if response.status_code >= 500:
            log_level = "error"
        elif response.status_code >= 400:
            log_level = "warning"
        else:
            log_level = "info"
            
        # 记录响应信息
        getattr(log_instance, log_level)(
            f"Request completed: {request.method} {request.path} "
            f"Status: {response.status_code} "
            f"Duration: {duration:.3f}s "
            f"Size: {response.content_length or 0} bytes"
        )
        
        return response
    
    @app.errorhandler(Exception)
    def log_exception(e):
        """记录异常"""
        log_instance.error(
            f"Unhandled exception in {request.method} {request.path}: {str(e)}",
            exc_info=True
        )
        return {"error": "Internal Server Error"}, 500


def create_app_with_unified_logging(config=None):
    """
    创建带有统一日志系统的Flask应用
    """
    global _region_data_synced
    global _cookie_data_synced
    global _config_initialized
    
    # 首先设置统一日志系统
    unified_log = setup_unified_logger()
    
    app = Flask(__name__)
    
    # 设置Flask请求日志
    setup_flask_request_logging(app, unified_log)
    
    # 配置跨域
    CORS(app, supports_credentials=True)
    
    # 其余配置保持不变...
    # ... (原有的Swagger配置、蓝图注册等)
    
    # 使用统一的日志实例
    unified_log.info("Flask应用启动，使用统一日志系统")
    
    return app, unified_log


# 日志配置类
class LogConfig:
    """日志配置管理"""
    
    def __init__(self):
        self.console_max_logs = int(os.getenv('LOG_CONSOLE_MAX', 3000))
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_retention = int(os.getenv('LOG_RETENTION_DAYS', 7))
        self.enable_request_logging = os.getenv('LOG_REQUESTS', 'true').lower() == 'true'
        self.enable_sql_logging = os.getenv('LOG_SQL', 'false').lower() == 'true'
    
    def get_filters(self):
        """获取日志过滤器配置"""
        return {
            'skip_health_check': True,
            'skip_static_files': True,
            'min_duration_ms': int(os.getenv('LOG_MIN_DURATION_MS', 100)),
        }


# 导出统一的日志实例
log_config = LogConfig()
log = setup_unified_logger(log_config.console_max_logs)


# 数据库日志装饰器
def log_database_operation(operation_name: str):
    """
    数据库操作日志装饰器
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not log_config.enable_sql_logging:
                return func(*args, **kwargs)
                
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                log.debug(f"DB {operation_name}: {duration:.3f}s - Success")
                return result
            except Exception as e:
                duration = time.time() - start_time
                log.error(f"DB {operation_name}: {duration:.3f}s - Error: {str(e)}")
                raise
        return wrapper
    return decorator


# 任务日志装饰器
def log_task_operation(task_name: str):
    """
    任务操作日志装饰器
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            task_id = kwargs.get('task_id') or (args[0] if args else 'unknown')
            
            log.info(f"Task {task_name} started: {task_id}")
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                log.info(f"Task {task_name} completed: {task_id} ({duration:.3f}s)")
                return result
            except Exception as e:
                duration = time.time() - start_time
                log.error(f"Task {task_name} failed: {task_id} ({duration:.3f}s) - {str(e)}")
                raise
        return wrapper
    return decorator


# 使用示例
if __name__ == "__main__":
    # 创建应用和统一日志
    app, unified_log = create_app_with_unified_logging()
    
    # 在定时任务中使用统一日志
    def check_cookie_status():
        """检查所有cookie的状态，解封可用的cookie"""
        try:
            unified_log.info("开始检查cookie状态...")
            # ... 原有逻辑
            unified_log.info("Cookie状态检查完成")
        except Exception as e:
            unified_log.error(f"检查cookie状态时出错: {e}")
    
    # 启动应用
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    unified_log.info(f"启动应用，地址: http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)