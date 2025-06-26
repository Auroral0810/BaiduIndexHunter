#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试从MySQL中读取cookie并组装成正确的cookie字典格式
"""
import sys
import os
import json


# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from config.settings import MYSQL_CONFIG

# 直接实现MySQL连接和cookie组装功能
import pymysql
from pymysql.cursors import DictCursor


def get_assembled_cookies():
    """
    获取所有可用账号的完整cookie字典
    :return: 完整的cookie字典列表，每个字典代表一个账号的完整cookie
    """
    # 连接数据库
    try:
        connection = pymysql.connect(
            host=MYSQL_CONFIG['host'],
            port=MYSQL_CONFIG['port'],
            user=MYSQL_CONFIG['user'],
            password=MYSQL_CONFIG['password'],
            db=MYSQL_CONFIG['db'],
            charset='utf8mb4',
            cursorclass=DictCursor
        )
        print(f"成功连接到MySQL数据库: {MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}")
    except Exception as e:
        print(f"MySQL连接失败: {e}")
        return []
    
    # 获取所有可用的cookie
    try:
        with connection.cursor() as cursor:
            # 查询所有可用的cookie
            sql = "SELECT * FROM cookies WHERE is_available = TRUE"
            cursor.execute(sql)
            cookies = cursor.fetchall()
            
            # 按account_id分组
            grouped_cookies = {}
            for cookie in cookies:
                account_id = cookie['account_id']
                if account_id not in grouped_cookies:
                    grouped_cookies[account_id] = []
                grouped_cookies[account_id].append(cookie)
            
            # 组装cookie
            assembled_cookies = []
            for account_id, cookies in grouped_cookies.items():
                cookie_dict = {}
                for cookie in cookies:
                    cookie_dict[cookie['cookie_name']] = cookie['cookie_value']
                
                if cookie_dict:  # 只添加非空的cookie字典
                    assembled_cookies.append({
                        'account_id': account_id,
                        'cookie_dict': cookie_dict
                    })
            
            print(f"从数据库获取并组装了 {len(assembled_cookies)} 个完整cookie")
            return assembled_cookies
    except Exception as e:
        print(f"获取cookie失败: {e}")
        return []
    finally:
        connection.close()


def test_cookie_assembly():
    """测试cookie组装功能"""
    print("=" * 50)
    print("测试从MySQL中读取cookie并组装成正确的cookie字典格式")
    print("=" * 50)
    
    # 获取组装好的cookie
    assembled_cookies = get_assembled_cookies()
    
    if not assembled_cookies:
        print("未找到可用的cookie，请检查数据库")
        return
    
    print(f"成功获取 {len(assembled_cookies)} 个完整cookie")
    
    # 打印每个cookie的详细信息
    for i, cookie_data in enumerate(assembled_cookies, 1):
        account_id = cookie_data['account_id']
        cookie_dict = cookie_data['cookie_dict']
        
        print(f"\n--- Cookie #{i} (Account ID: {account_id}) ---")
        print(f"Cookie包含 {len(cookie_dict)} 个字段")
        
        # 打印cookie字典的格式化输出
        print("Cookie字典格式:")
        print("cookies = {")
        for key, value in cookie_dict.items():
            print(f"    '{key}': '{value}',")
        print("}")
        
        # 如果cookie太多，只显示前3个
        if i >= 3:
            print(f"\n... 还有 {len(assembled_cookies) - 3} 个cookie未显示 ...")
            break
    
    # 测试cookie是否可以正确序列化为JSON
    try:
        json_str = json.dumps(assembled_cookies[0]['cookie_dict'])
        print("\nCookie可以正确序列化为JSON:")
        print(json_str[:100] + "..." if len(json_str) > 100 else json_str)
    except Exception as e:
        print(f"\nCookie序列化为JSON失败: {e}")
    
    print("\n测试完成！")


if __name__ == "__main__":
    test_cookie_assembly() 