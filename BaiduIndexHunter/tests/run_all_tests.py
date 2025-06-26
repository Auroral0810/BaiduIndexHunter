"""
运行所有测试的主文件
"""
import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import log
from tests.test_logger import run_all_tests as test_logger
from tests.test_mysql_manager import run_all_tests as test_mysql
from tests.test_redis_manager import run_all_tests as test_redis
from tests.test_cookie_validator import run_all_tests as test_validator
from tests.test_cookie_rotator import run_all_tests as test_rotator


def run_all_tests():
    """运行所有测试"""
    log.info("=" * 50)
    log.info("开始运行百度指数爬虫项目所有测试")
    log.info("=" * 50)
    
    # 测试日志模块
    log.info("\n\n" + "=" * 30 + " 测试日志模块 " + "=" * 30)
    test_logger()
    
    # 测试MySQL模块
    log.info("\n\n" + "=" * 30 + " 测试MySQL模块 " + "=" * 30)
    test_mysql()
    
    # 测试Redis模块
    log.info("\n\n" + "=" * 30 + " 测试Redis模块 " + "=" * 30)
    test_redis()
    
    # 测试Cookie验证模块
    log.info("\n\n" + "=" * 30 + " 测试Cookie验证模块 " + "=" * 30)
    test_validator()
    
    # 测试Cookie轮换模块
    log.info("\n\n" + "=" * 30 + " 测试Cookie轮换模块 " + "=" * 30)
    test_rotator()
    
    log.info("\n\n" + "=" * 50)
    log.info("所有测试完成")
    log.info("=" * 50)


if __name__ == "__main__":
    run_all_tests() 