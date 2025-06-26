"""
Redis缓存管理模块测试
"""
import sys
import os
import json
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.redis_manager import redis_manager
from utils.logger import log


def test_connection():
    """测试Redis连接"""
    log.info("=== 测试Redis连接 ===")
    # 连接已在redis_manager初始化时建立
    if redis_manager.client:
        try:
            redis_manager.client.ping()
            log.info("Redis连接成功")
            return True
        except Exception as e:
            log.error(f"Redis连接失败: {e}")
            return False
    else:
        log.error("Redis客户端未初始化")
        return False


def test_cache_cookie():
    """测试缓存Cookie"""
    log.info("=== 测试缓存Cookie ===")
    
    # 创建测试Cookie数据
    test_cookie_id = "test_cookie_123"
    test_cookie_data = {
        'id': test_cookie_id,
        'account_id': 'test_account',
        'cookie_name': 'BDUSS',
        'cookie_value': 'test_cookie_value_123456',
        'expire_time': None,
    }
    
    # 缓存Cookie
    result = redis_manager.cache_cookie(test_cookie_id, test_cookie_data)
    log.info(f"缓存Cookie结果: {result}")
    
    return test_cookie_id, result


def test_get_cookie(cookie_id):
    """测试获取缓存的Cookie"""
    log.info("=== 测试获取缓存Cookie ===")
    
    cookie_data = redis_manager.get_cookie(cookie_id)
    
    if cookie_data:
        log.info(f"获取到Cookie: {cookie_data}")
        return True
    else:
        log.warning(f"未获取到Cookie: {cookie_id}")
        return False


def test_record_usage_and_success(cookie_id):
    """测试记录Cookie使用情况和成功率"""
    log.info("=== 测试记录Cookie使用情况 ===")
    
    # 记录使用次数
    for _ in range(5):
        redis_manager.record_cookie_usage(cookie_id)
    log.info(f"记录了5次Cookie使用")
    
    # 记录成功/失败
    redis_manager.record_cookie_success(cookie_id, True)  # 成功
    redis_manager.record_cookie_success(cookie_id, True)  # 成功
    redis_manager.record_cookie_success(cookie_id, False)  # 失败
    log.info(f"记录了2次成功，1次失败")
    
    # 获取指标
    metrics = redis_manager.get_cookie_metrics(cookie_id)
    log.info(f"Cookie指标: {metrics}")
    
    return metrics


def test_remove_cookie(cookie_id):
    """测试移除Cookie"""
    log.info("=== 测试移除Cookie ===")
    
    result = redis_manager.remove_cookie(cookie_id)
    log.info(f"移除Cookie结果: {result}")
    
    # 验证是否已移除
    cookie_data = redis_manager.get_cookie(cookie_id)
    if not cookie_data:
        log.info(f"Cookie已成功移除")
        return True
    else:
        log.warning(f"Cookie未成功移除")
        return False


def run_all_tests():
    """运行所有测试"""
    log.info("开始Redis管理器测试...")
    
    # 测试连接
    if not test_connection():
        log.error("Redis连接失败，终止测试")
        return
    
    # 测试缓存Cookie
    cookie_id, cache_result = test_cache_cookie()
    if not cache_result:
        log.error("缓存Cookie失败，终止测试")
        return
    
    # 测试获取Cookie
    get_result = test_get_cookie(cookie_id)
    if not get_result:
        log.error("获取Cookie失败，终止测试")
        return
    
    # 测试记录使用情况
    metrics = test_record_usage_and_success(cookie_id)
    
    # 测试移除Cookie
    remove_result = test_remove_cookie(cookie_id)
    
    log.info("Redis管理器测试完成")


if __name__ == "__main__":
    run_all_tests() 