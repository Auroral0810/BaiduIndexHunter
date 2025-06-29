"""
Cookie验证模块测试
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cookie_manager.cookie_validator import cookie_validator
from db.mysql_manager import mysql_manager
from utils.logger import log


def test_validate_invalid_cookie():
    """测试验证无效Cookie"""
    log.info("=== 测试验证无效Cookie ===")
    
    # 创建一个明显无效的Cookie
    invalid_cookie = "BDUSS=invalid_cookie_value"
    
    # 验证Cookie
    is_valid, reason = cookie_validator.validate_cookie(invalid_cookie)
    
    log.info(f"无效Cookie验证结果: {is_valid}, 原因: {reason}")
    return is_valid, reason


def test_validate_real_cookies():
    """测试验证数据库中的真实Cookie"""
    log.info("=== 测试验证真实Cookie ===")
    
    # 获取数据库中的可用Cookie
    cookies = mysql_manager.get_available_cookies()
    if not cookies:
        log.warning("数据库中没有可用的Cookie，跳过真实Cookie验证测试")
        return []
    
    results = []
    
    # 测试前3个Cookie（如果有）
    for i, cookie in enumerate(cookies[:3]):
        log.info(f"验证Cookie {i+1}: ID={cookie['id']}, 账号={cookie['account_id']}")
        
        # 验证Cookie
        is_valid, reason = cookie_validator.validate_cookie(cookie['cookie_value'])
        
        status = "有效" if is_valid else "无效"
        log.info(f"Cookie {cookie['id']} 验证结果: {status}, " + (f"原因: {reason}" if not is_valid else ""))
        
        results.append({
            'id': cookie['id'],
            'account_id': cookie['account_id'],
            'is_valid': is_valid,
            'reason': reason
        })
    
    return results


def test_parse_cookie_string():
    """测试解析Cookie字符串"""
    log.info("=== 测试解析Cookie字符串 ===")
    
    # 测试标准Cookie字符串
    standard_cookie = "BDUSS=abc123; BAIDUID=xyz789; PSTM=1600000000"
    parsed_standard = cookie_validator._parse_cookie_string(standard_cookie)
    log.info(f"标准Cookie解析结果: {parsed_standard}")
    
    # 测试JSON格式Cookie字符串
    json_cookie = '{"BDUSS": "abc123", "BAIDUID": "xyz789", "PSTM": "1600000000"}'
    parsed_json = cookie_validator._parse_cookie_string(json_cookie)
    log.info(f"JSON Cookie解析结果: {parsed_json}")
    
    # 测试空Cookie字符串
    empty_cookie = ""
    parsed_empty = cookie_validator._parse_cookie_string(empty_cookie)
    log.info(f"空Cookie解析结果: {parsed_empty}")
    
    return parsed_standard, parsed_json, parsed_empty


def run_all_tests():
    """运行所有测试"""
    log.info("开始Cookie验证器测试...")
    
    # 测试无效Cookie验证
    test_validate_invalid_cookie()
    
    # 测试解析Cookie字符串
    test_parse_cookie_string()
    
    # 测试验证真实Cookie
    real_results = test_validate_real_cookies()
    
    # 输出总结
    valid_count = sum(1 for r in real_results if r['is_valid'])
    log.info(f"真实Cookie验证结果: {valid_count}/{len(real_results)} 有效")
    
    log.info("Cookie验证器测试完成")


if __name__ == "__main__":
    run_all_tests() 