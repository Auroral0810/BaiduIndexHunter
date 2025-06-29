"""
Cookie轮换模块测试
"""
import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cookie_manager.cookie_rotator import cookie_rotator
from db.mysql_manager import mysql_manager
from db.redis_manager import redis_manager
from utils.logger import log


def test_load_cookies_from_db():
    """测试从数据库加载Cookie"""
    log.info("=== 测试从数据库加载Cookie ===")
    
    # 清空Redis缓存中的Cookie
    cached_ids = redis_manager.get_all_cached_cookie_ids()
    for cookie_id in cached_ids:
        redis_manager.remove_cookie(cookie_id)
    
    # 调用私有方法加载Cookie
    cookie_rotator._refresh_cookies_from_db()
    
    # 检查加载结果
    cached_ids = redis_manager.get_all_cached_cookie_ids()
    log.info(f"从数据库加载了 {len(cached_ids)} 个Cookie到缓存")
    
    return cached_ids


def test_get_cookie():
    """测试获取Cookie"""
    log.info("=== 测试获取Cookie ===")
    
    # 获取Cookie
    cookie_id, cookie_value = cookie_rotator.get_cookie()
    
    if cookie_id and cookie_value:
        log.info(f"获取到Cookie: ID={cookie_id}")
        cookie_str = str(cookie_value)
        log.debug(f"Cookie值: {cookie_str[:30]}...")  # 转换为字符串后只显示前30个字符
        return True
    else:
        log.warning("未获取到可用的Cookie")
        return False


def test_select_best_cookie():
    """测试选择最佳Cookie"""
    log.info("=== 测试选择最佳Cookie ===")
    
    # 获取所有缓存的Cookie ID
    cached_ids = redis_manager.get_all_cached_cookie_ids()
    
    if not cached_ids:
        log.warning("缓存中没有Cookie，无法测试选择最佳Cookie")
        return None
    
    # 模拟使用情况
    for i, cookie_id in enumerate(cached_ids):
        # 记录不同的使用次数
        for _ in range(i + 1):
            redis_manager.record_cookie_usage(cookie_id)
        
        # 记录不同的成功率
        success_count = max(1, i)
        fail_count = max(0, 3 - i)
        
        for _ in range(success_count):
            redis_manager.record_cookie_success(cookie_id, True)
        
        for _ in range(fail_count):
            redis_manager.record_cookie_success(cookie_id, False)
    
    # 多次选择最佳Cookie，检查分布
    selection_counts = {}
    for _ in range(20):
        best_id = cookie_rotator._select_least_used_cookie(cached_ids)
        selection_counts[best_id] = selection_counts.get(best_id, 0) + 1
    
    log.info(f"20次选择的分布: {selection_counts}")
    
    return selection_counts


def test_report_cookie_status():
    """测试报告Cookie状态"""
    log.info("=== 测试报告Cookie状态 ===")
    
    # 获取一个Cookie
    cookie_id, _ = cookie_rotator.get_cookie()
    
    if not cookie_id:
        log.warning("未获取到Cookie，无法测试报告状态")
        return False
    
    # 报告成功状态
    log.info(f"报告Cookie {cookie_id} 成功状态")
    cookie_rotator.report_cookie_status(cookie_id, True)
    
    # 获取指标
    metrics = redis_manager.get_cookie_metrics(cookie_id)
    log.info(f"报告成功后的指标: {metrics}")
    
    # 报告失败状态
    log.info(f"报告Cookie {cookie_id} 失败状态")
    cookie_rotator.report_cookie_status(cookie_id, False)
    
    # 获取指标
    metrics = redis_manager.get_cookie_metrics(cookie_id)
    log.info(f"报告失败后的指标: {metrics}")
    
    return True


def run_all_tests():
    """运行所有测试"""
    log.info("开始Cookie轮换器测试...")
    
    # 测试从数据库加载Cookie
    cached_ids = test_load_cookies_from_db()
    if not cached_ids:
        log.error("从数据库加载Cookie失败，终止测试")
        return
    
    # 测试获取Cookie
    if not test_get_cookie():
        log.error("获取Cookie失败，终止测试")
        return
    
    # 测试选择最佳Cookie
    test_select_best_cookie()
    
    # 测试报告Cookie状态
    test_report_cookie_status()
    
    log.info("Cookie轮换器测试完成")


if __name__ == "__main__":
    run_all_tests() 