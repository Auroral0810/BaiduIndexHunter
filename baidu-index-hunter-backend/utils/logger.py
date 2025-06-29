"""
日志工具模块，正确
"""
import sys
import os
from pathlib import Path
from loguru import logger
from config.settings import LOG_LEVEL, LOG_DIR, LOG_RETENTION
from collections import deque


class LoggerWithCache:
    """带有消息缓存的日志器"""
    
    def __init__(self, base_logger, console_max_logs=2000):
        self._logger = base_logger
        self._message_cache = deque(maxlen=500)  # 最多保存最近50条消息
        self._console_log_count = 0  # 控制台日志计数器
        self._console_max_logs = console_max_logs  # 控制台最大日志数量
    
    def _check_and_clear_console(self):
        """检查并在必要时清空控制台"""
        self._console_log_count += 1
        if self._console_log_count >= self._console_max_logs:
            # 清空控制台 (ANSI 转义序列)
            print("\033c", end="")
            # 重置计数器
            self._console_log_count = 0
    
    def info(self, message, *args, **kwargs):
        self._message_cache.append(("INFO", message))
        # self._check_and_clear_console()
        return self._logger.info(message, *args, **kwargs)
    
    def debug(self, message, *args, **kwargs):
        self._message_cache.append(("DEBUG", message))
        # self._check_and_clear_console()
        return self._logger.debug(message, *args, **kwargs)
    
    def warning(self, message, *args, **kwargs):
        self._message_cache.append(("WARNING", message))
        # self._check_and_clear_console()
        return self._logger.warning(message, *args, **kwargs)
    
    def error(self, message, *args, **kwargs):
        self._message_cache.append(("ERROR", message))
        # self._check_and_clear_console()
        return self._logger.error(message, *args, **kwargs)
    
    def critical(self, message, *args, **kwargs):
        self._message_cache.append(("CRITICAL", message))
        # self._check_and_clear_console()
        return self._logger.critical(message, *args, **kwargs)
    
    def last_message(self, level=None):
        """
        获取最近的日志消息
        :param level: 日志级别，如果指定则只返回该级别的消息
        :return: 最近的日志消息
        """
        if not self._message_cache:
            return ""
            
        if level:
            # 从后向前查找指定级别的消息
            for msg_level, message in reversed(self._message_cache):
                if msg_level == level.upper():
                    return message
            return ""
        else:
            # 返回最近的消息，不考虑级别
            return self._message_cache[-1][1]
    
    def last_error_message(self):
        """获取最近的错误消息"""
        return self.last_message(level="ERROR")
    
    def __getattr__(self, name):
        # 委托其他方法给原始logger
        return getattr(self._logger, name)


def setup_logger(console_max_logs=100):
    """
    配置日志系统
    :param console_max_logs: 控制台最大日志数量，达到后自动清空
    """
    # 清除默认处理程序
    logger.remove()
    
    # 添加控制台输出
    logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )
    
    # 添加文件输出
    log_file = LOG_DIR / "baidu_index_hunter_{time:YYYY-MM-DD}.log"
    logger.add(
        log_file,
        rotation="00:00",  # 每天零点切换日志文件
        retention=LOG_RETENTION,  # 保留天数
        level=LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        encoding="utf-8",
    )
    
    return LoggerWithCache(logger, console_max_logs)


# 导出日志实例
log = setup_logger() 