"""
日志模块测试
"""
import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import log


def test_log_levels():
    """测试各级别日志输出"""
    log.info("=== 测试日志级别 ===")
    
    log.debug("这是一条调试日志")
    log.info("这是一条信息日志")
    log.success("这是一条成功日志")
    log.warning("这是一条警告日志")
    log.error("这是一条错误日志")
    log.critical("这是一条严重错误日志")


def test_log_exception():
    """测试异常日志"""
    log.info("=== 测试异常日志 ===")
    
    try:
        # 故意制造一个异常
        result = 1 / 0
    except Exception as e:
        log.exception(f"捕获到异常: {e}")


def test_log_context():
    """测试日志上下文"""
    log.info("=== 测试日志上下文 ===")
    
    # 添加上下文信息
    with log.contextualize(user_id="test_user", action="test_action"):
        log.info("这是带有上下文的日志")
        log.warning("这是另一条带有相同上下文的日志")


def test_log_format():
    """测试日志格式"""
    log.info("=== 测试日志格式 ===")
    
    # 测试不同格式的日志
    log.info("普通信息日志")
    log.info("包含数字的日志: {}", 123)
    log.info("包含多个参数的日志: {} 和 {}", "参数1", "参数2")
    log.info("包含字典的日志: {}", {"key": "value"})
    log.info("包含列表的日志: {}", [1, 2, 3])


def run_all_tests():
    """运行所有测试"""
    log.info("开始日志模块测试...")
    
    # 运行各测试
    test_log_levels()
    test_log_exception()
    test_log_context()
    test_log_format()
    
    log.info("日志模块测试完成")
    log.info("请检查日志文件以确认日志是否正确写入文件")


if __name__ == "__main__":
    run_all_tests() 