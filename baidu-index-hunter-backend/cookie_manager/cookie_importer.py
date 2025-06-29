#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
导入cookie数据到数据库的脚本
解析Excel文件中的cookie数据并保存到MySQL数据库中
"""

import os
import sys
import pandas as pd
import mysql.connector
from datetime import datetime
import re

# 添加项目根目录到路径，以便导入项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目配置
from config.settings import MYSQL_CONFIG

def parse_cookie_string(cookie_str):
    """
    解析完整的cookie字符串为键值对列表
    :param cookie_str: 完整的cookie字符串，如 'name1=value1; name2=value2'
    :return: cookie名称和值的列表 [(name1, value1), (name2, value2), ...]
    """
    cookie_pairs = []
    if not cookie_str or not isinstance(cookie_str, str):
        return cookie_pairs
    
    # 按分号分割cookie
    parts = cookie_str.split(';')
    for part in parts:
        part = part.strip()
        if '=' in part:
            # 找到第一个等号作为分隔符
            split_index = part.find('=')
            name = part[:split_index].strip()
            value = part[split_index+1:].strip()
            if name:
                cookie_pairs.append((name, value))
    
    return cookie_pairs

def read_excel_file(file_path):
    """
    读取Excel文件中的cookie数据
    :param file_path: Excel文件路径
    :return: cookie数据列表
    """
    try:
        # 尝试读取Excel文件
        df = pd.read_excel(file_path)
        print(f"成功读取Excel文件: {file_path}")
        print(f"数据行数: {len(df)}")
        
        # 显示Excel文件的列名，以便确认格式
        print(f"列名: {df.columns.tolist()}")
        
        return df
    except Exception as e:
        print(f"读取Excel文件失败: {e}")
        return None

def connect_to_db():
    """
    连接到MySQL数据库
    :return: 数据库连接和游标
    """
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        print(f"成功连接到MySQL数据库: {MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}")
        return conn, cursor
    except Exception as e:
        print(f"连接数据库失败: {e}")
        return None, None

def import_cookies_from_excel(file_path):
    """
    从Excel文件导入cookie数据到数据库
    :param file_path: Excel文件路径
    """
    # 读取Excel文件
    df = read_excel_file(file_path)
    if df is None:
        return
    
    # 连接数据库
    conn, cursor = connect_to_db()
    if conn is None or cursor is None:
        return
    
    try:
        # 读取Excel文件中的数据并导入数据库
        total_cookies = 0
        processed_accounts = set()
        
        # 检查文件内容，确定导入方式
        # 1. 首先检查是否已经是按cookie名称和值分开的格式
        if {'account_id', 'cookie_name', 'cookie_value'}.issubset(set(df.columns.str.lower())):
            # 已经是按cookie名称和值分开的格式，直接导入
            print("使用已分好的cookie名称和值的格式导入...")
            
            for _, row in df.iterrows():
                account_id = row['account_id']
                cookie_name = row['cookie_name']
                cookie_value = str(row['cookie_value'])  # 确保cookie_value是字符串
                
                # 获取过期时间，如果有的话
                expire_time = None
                if 'expire_time' in df.columns:
                    expire_time = row['expire_time']
                    if pd.isna(expire_time):
                        expire_time = None
                
                # 插入到数据库
                sql = """
                INSERT INTO cookies 
                (account_id, cookie_name, cookie_value, expire_time)
                VALUES (%s, %s, %s, %s)
                """
                try:
                    cursor.execute(sql, (account_id, cookie_name, cookie_value, expire_time))
                    total_cookies += 1
                    processed_accounts.add(account_id)
                except Exception as e:
                    print(f"插入cookie失败: {e} - {account_id}, {cookie_name}")
        
        # 2. 如果不是上述格式，尝试解析完整cookie字符串
        else:
            print("尝试解析完整cookie字符串格式...")
            
            # 查找可能包含完整cookie字符串的列
            cookie_column = None
            for col in df.columns:
                if 'cookie' in col.lower() or 'cookie_str' in col.lower():
                    cookie_column = col
                    break
            
            # 如果找不到可能的cookie列，使用第一个包含文本的列
            if cookie_column is None:
                for col in df.columns:
                    if df[col].dtype == 'object':
                        cookie_column = col
                        break
            
            if cookie_column is None:
                print("无法找到包含cookie数据的列")
                return
            
            print(f"使用列 '{cookie_column}' 作为cookie数据源")
            
            # 为每条cookie分配account_id
            counter = 1
            for idx, row in df.iterrows():
                cookie_str = row[cookie_column]
                if pd.isna(cookie_str) or not cookie_str:
                    continue
                
                # 构建account_id
                account_id = f"cookie_{counter}"
                counter += 1
                
                # 解析cookie字符串
                cookie_pairs = parse_cookie_string(str(cookie_str))
                
                for name, value in cookie_pairs:
                    sql = """
                    INSERT INTO cookies 
                    (account_id, cookie_name, cookie_value)
                    VALUES (%s, %s, %s)
                    """
                    try:
                        cursor.execute(sql, (account_id, name, value))
                        total_cookies += 1
                        processed_accounts.add(account_id)
                    except Exception as e:
                        print(f"插入cookie失败: {e} - {account_id}, {name}")
        
        # 提交事务
        conn.commit()
        print(f"成功导入 {total_cookies} 条cookie数据，共计 {len(processed_accounts)} 个账号")
    
    except Exception as e:
        print(f"导入cookie数据失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def import_80_cookies_from_file():
    """
    从80个cookie文件导入数据，处理特定文件格式
    """
    file_path = '/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/cookie_manager/80个cookie.xlsx'
    
    # 读取Excel文件
    try:
        df = pd.read_excel(file_path)
        print(f"成功读取Excel文件: {file_path}")
        print(f"数据行数: {len(df)}")
    except Exception as e:
        print(f"读取Excel文件失败: {e}")
        return
    
    # 连接数据库
    conn, cursor = connect_to_db()
    if conn is None or cursor is None:
        return
    
    try:
        # 计数器
        total_cookies = 0
        processed_accounts = set()
        
        # 遍历所有行
        for _, row in df.iterrows():
            # 获取cookie字符串
            cookie_str = str(row.iloc[0]) if not pd.isna(row.iloc[0]) else ""
            
            if not cookie_str or cookie_str.isspace():
                continue
            
            # 从cookie字符串中提取出单个cookie
            cookie_pairs = parse_cookie_string(cookie_str)
            
            # 使用从第一个cookie名称中提取的账号作为account_id
            account_id = None
            for name, value in cookie_pairs:
                if name == "BDUSS":
                    # 提取BDUSS用作account_id的一部分
                    account_id = f"cookie_{len(processed_accounts) + 1}"
                    break
            
            # 如果没有找到BDUSS，使用默认的account_id
            if not account_id:
                account_id = f"cookie_{len(processed_accounts) + 1}"
            
            # 保存到数据库
            for name, value in cookie_pairs:
                sql = """
                INSERT INTO cookies 
                (account_id, cookie_name, cookie_value)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE cookie_value = VALUES(cookie_value)
                """
                try:
                    cursor.execute(sql, (account_id, name, value))
                    total_cookies += 1
                except Exception as e:
                    print(f"插入cookie失败: {e} - {account_id}, {name}")
            
            processed_accounts.add(account_id)
        
        # 提交事务
        conn.commit()
        print(f"成功导入 {total_cookies} 条cookie数据，共计 {len(processed_accounts)} 个账号")
    
    except Exception as e:
        print(f"导入cookie数据失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # 获取命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='导入cookie数据到数据库')
    parser.add_argument('--file', type=str, help='Excel文件路径，默认为80个cookie.xlsx')
    parser.add_argument('--mode', type=str, default='auto', choices=['auto', '80cookies'],
                        help='导入模式: auto-自动检测格式, 80cookies-专门处理80个cookie.xlsx')
    
    args = parser.parse_args()
    
    if args.mode == '80cookies' or (not args.file and args.mode == 'auto'):
        print("使用80cookies模式导入...")
        import_80_cookies_from_file()
    elif args.file:
        print(f"使用自动模式导入文件: {args.file}")
        import_cookies_from_excel(args.file)
    else:
        print("请提供Excel文件路径或选择80cookies模式") 