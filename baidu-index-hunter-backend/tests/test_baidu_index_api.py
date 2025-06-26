"""
百度指数API模块测试
"""
import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from spider.baidu_index_api import baidu_index_api
from utils.logger import log


def test_search_index():
    """测试搜索指数API"""
    log.info("=== 测试搜索指数API ===")
    
    # 测试关键词
    keywords = ["百度", "阿里巴巴", "腾讯"]
    
    # 获取搜索指数
    result = baidu_index_api.get_search_index(keywords)
    
    if result:
        log.info(f"搜索指数API测试成功")
        # 打印部分结果
        log.info(f"结果包含 {len(result)} 个关键词的数据")
        return True
    else:
        log.error("搜索指数API测试失败")
        return False


def test_trend_index():
    """测试趋势指数API"""
    log.info("=== 测试趋势指数API ===")
    
    # 测试关键词
    keywords = ["百度", "阿里巴巴"]
    
    # 获取趋势指数
    result = baidu_index_api.get_trend_index(keywords)
    
    if result:
        log.info(f"趋势指数API测试成功")
        # 打印部分结果
        log.info(f"结果包含 {len(result)} 个关键词的数据")
        return True
    else:
        log.error("趋势指数API测试失败")
        return False


def test_parse_cookie_string():
    """测试解析Cookie字符串"""
    log.info("=== 测试解析Cookie字符串 ===")
    
    # 测试标准Cookie字符串
    standard_cookie = "BDUSS=abc123; BAIDUID=xyz789; PSTM=1600000000"
    parsed_standard = baidu_index_api.parse_cookie_string(standard_cookie)
    log.info(f"标准Cookie解析结果: {parsed_standard}")
    
    # 测试JSON格式Cookie字符串
    json_cookie = '{"BDUSS": "abc123", "BAIDUID": "xyz789", "PSTM": "1600000000"}'
    parsed_json = baidu_index_api.parse_cookie_string(json_cookie)
    log.info(f"JSON Cookie解析结果: {parsed_json}")
    
    # 测试空Cookie字符串
    empty_cookie = ""
    parsed_empty = baidu_index_api.parse_cookie_string(empty_cookie)
    log.info(f"空Cookie解析结果: {parsed_empty}")
    
    return parsed_standard, parsed_json, parsed_empty


def run_all_tests():
    """运行所有测试"""
    log.info("开始百度指数API测试...")
    
    # 测试解析Cookie字符串
    test_parse_cookie_string()
    
    # 测试搜索指数API
    search_result = test_search_index()
    
    # 如果搜索指数API测试成功，再测试趋势指数API
    if search_result:
        test_trend_index()
    
    log.info("百度指数API测试完成")


if __name__ == "__main__":
    run_all_tests() 