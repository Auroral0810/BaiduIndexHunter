# 检测可用的cookie

import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import time
from fake_useragent import UserAgent
import execjs
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from db.mysql_manager import mysql_manager
from utils.logger import log

ua = UserAgent()
useragent = ua.random  # 随机生成浏览器的useragent

# 测试每个 cookie 组是否被锁定
def test_cookies():
    blocked_accounts = []
    valid_accounts = []
    
    # 测试参数（使用固定的请求参数）
    city_number = 1  # 济南
    word = "电脑"
    
    # 计算日期范围（最近30天）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    startDate = start_date.strftime("%Y-%m-%d")
    endDate = end_date.strftime("%Y-%m-%d")
    
    print("开始测试所有数据库中的cookie...")
    
    # 连接MySQL数据库
    if not mysql_manager.connect():
        print("连接MySQL数据库失败，无法测试cookie")
        return [], []
    
    # 从数据库获取所有组装好的cookie
    assembled_cookies = mysql_manager.get_assembled_cookies()
    
    if not assembled_cookies:
        print("数据库中没有可用的cookie")
        return [], []
    
    print(f"从数据库获取到 {len(assembled_cookies)} 个cookie组")
    
    for cookie_data in assembled_cookies:
        account_id = cookie_data['account_id']
        cookie_dict = cookie_data['cookie_dict']
        
        print(f"测试账户: {account_id}")
        
        try:
            # 构建请求URL
            url = f'https://index.baidu.com/api/SearchApi/index?area={city_number}&word=[[{{"name":"{word}","wordType":1}}]]&startDate={startDate}&endDate={endDate}'
            url_cipyter = f'https://index.baidu.com/v2/main/index.html#/trend/{word}?words={word}'
            
            # 获取cipher-text
            try:
                with open('/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/utils/Cipher-Text.js', 'r') as f:
                    js = f.read()
                    ctx = execjs.compile(js)
                cipyer_text = ctx.call('ascToken', url_cipyter,useragent)
            except Exception as e:
                print(f"生成cipher-text失败: {e}")
                cipyer_text = ""
            
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Cache-Control': 'no-cache',
                'Cipher-Text': cipyer_text,
                'Connection': 'keep-alive',
                'Pragma': 'no-cache',
                'Referer': 'https://index.baidu.com/v2/main/index.html',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': useragent,
                'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
            }

            # 发送请求获取数据
            response = requests.get(url, cookies=cookie_dict, headers=headers)
            result = response.json()
            
            # 打印返回结果
            print(f"返回结果: {json.dumps(result, ensure_ascii=False)[:200]}...")
            
            # 检查是否被锁定或无效
            if result.get('status') == 10001 and result.get('message') == 'request block':
                print(f"账户 {account_id} 已被锁定！")
                blocked_accounts.append(account_id)
                # 更新数据库中的cookie状态
                mysql_manager.update_cookie_status(account_id, False)
            elif result.get('status') == 10000 and result.get('message') == 'not login':
                print(f"账户 {account_id} 未登录！")
                blocked_accounts.append(account_id)
                # 更新数据库中的cookie状态
                mysql_manager.update_cookie_status(account_id, False)
            elif result.get('status') == 10002 and result.get('message') == 'bad request':
                print(f"账户 {account_id} 请求错误！")
                blocked_accounts.append(account_id)
                # 更新数据库中的cookie状态
                mysql_manager.update_cookie_status(account_id, False)
            else:
                print(f"账户 {account_id} 正常可用")
                valid_accounts.append(account_id)
                # 更新数据库中的cookie状态
                mysql_manager.update_cookie_status(account_id, True)
                
        except Exception as e:
            print(f"测试账户 {account_id} 时出错: {str(e)}")
            # 出错时不改变cookie状态，可能是网络问题
            
        # 请求之间添加延时，避免频率过高
        time.sleep(0.05)
            
    print("\n测试结果汇总:")
    print(f"被锁定的账户: {blocked_accounts}")
    print(f"可用的账户: {valid_accounts}")
    
    # 关闭数据库连接
    mysql_manager.close()
    
    return blocked_accounts, valid_accounts


if __name__ == "__main__":
    # 执行 cookie 测试
    blocked_accounts, valid_accounts = test_cookies()
    
    # 将结果保存到文件
    with open('cookie_status.txt', 'w', encoding='utf-8') as f:
        f.write("被锁定的账户:\n")
        for account in blocked_accounts:
            f.write(f"{account}\n")
        
        f.write("\n可用的账户:\n")
        for account in valid_accounts:
            f.write(f"{account}\n")
    
    print(f"测试结果已保存到 cookie_status.txt 文件")

