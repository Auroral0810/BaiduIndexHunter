"""
MySQL数据库管理模块测试
"""
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.mysql_manager import mysql_manager
from utils.logger import log


def test_connection():
    """测试数据库连接"""
    log.info("=== 测试数据库连接 ===")
    result = mysql_manager.connect()
    log.info(f"数据库连接结果: {result}")
    return result


def test_get_all_cookies():
    """测试获取所有Cookie"""
    log.info("=== 测试获取所有Cookie ===")
    cookies = mysql_manager.get_all_cookies()
    log.info(f"获取到 {len(cookies)} 个Cookie记录")
    
    # 打印前3条记录（如果有）
    for i, cookie in enumerate(cookies[:3]):
        log.info(f"Cookie {i+1}: ID={cookie['id']}, 账号={cookie['account_id']}, 可用={cookie['is_available']}")
    
    return cookies


def test_get_available_cookies():
    """测试获取可用Cookie"""
    log.info("=== 测试获取可用Cookie ===")
    cookies = mysql_manager.get_available_cookies()
    log.info(f"获取到 {len(cookies)} 个可用Cookie记录")
    
    # 打印前3条记录（如果有）
    for i, cookie in enumerate(cookies[:3]):
        log.info(f"可用Cookie {i+1}: ID={cookie['id']}, 账号={cookie['account_id']}")
    
    return cookies


def test_update_cookie_status():
    """测试更新Cookie状态"""
    log.info("=== 测试更新Cookie状态 ===")
    
    # 获取第一个可用的Cookie（如果有）
    cookies = mysql_manager.get_available_cookies()
    if not cookies:
        log.warning("没有可用的Cookie，无法测试更新状态")
        return False
    
    cookie_id = cookies[0]['id']
    
    # 先将状态设为不可用
    log.info(f"将Cookie ID={cookie_id} 设为不可用")
    mysql_manager.update_cookie_status(cookie_id, False)
    
    # 再将状态设为可用
    log.info(f"将Cookie ID={cookie_id} 设为可用")
    result = mysql_manager.update_cookie_status(cookie_id, True)
    
    log.info(f"更新结果: 影响了 {result} 行")
    return result > 0


def test_update_cookie_value():
    """测试更新Cookie值"""
    log.info("=== 测试更新Cookie值 ===")
    
    # 获取第一个可用的Cookie（如果有）
    cookies = mysql_manager.get_available_cookies()
    if not cookies:
        log.warning("没有可用的Cookie，无法测试更新值")
        return False
    
    cookie_id = cookies[0]['id']
    original_value = cookies[0]['cookie_value']
    
    # 更新Cookie值（添加测试标记）
    test_value = original_value + "; _test_mark=1"
    log.info(f"更新Cookie ID={cookie_id} 的值")
    result = mysql_manager.update_cookie_value(cookie_id, test_value)
    
    # 恢复原始值
    mysql_manager.update_cookie_value(cookie_id, original_value)
    
    log.info(f"更新结果: 影响了 {result} 行")
    return result > 0


def test_get_cookie_by_account():
    """测试根据账号获取Cookie"""
    log.info("=== 测试根据账号获取Cookie ===")
    
    # 获取第一个Cookie的账号（如果有）
    cookies = mysql_manager.get_all_cookies()
    if not cookies:
        log.warning("没有Cookie记录，无法测试根据账号获取")
        return None
    
    account_id = cookies[0]['account_id']
    log.info(f"查询账号 {account_id} 的Cookie")
    
    cookie = mysql_manager.get_cookie_by_account(account_id)
    if cookie:
        log.info(f"找到Cookie: ID={cookie['id']}, 可用={cookie['is_available']}")
    else:
        log.warning(f"未找到账号 {account_id} 的Cookie")
    
    return cookie


def run_all_tests():
    """运行所有测试"""
    log.info("开始MySQL管理器测试...")
    
    # 测试连接
    if not test_connection():
        log.error("数据库连接失败，终止测试")
        return
    
    # 运行其他测试
    test_get_all_cookies()
    test_get_available_cookies()
    test_update_cookie_status()
    # test_update_cookie_value()
    test_get_cookie_by_account()
    
    # 关闭连接
    mysql_manager.close()
    log.info("MySQL管理器测试完成")


if __name__ == "__main__":
    run_all_tests() 