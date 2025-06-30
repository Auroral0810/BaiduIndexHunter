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
        time.sleep(2)
            
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


{
    'BAIDU_WISE_UID': 'wapp_1744869667916_527',
    'BAIDUID': 'FF85DF65CC7463F3726D5301B69C0672:FG=1',
    'BAIDUID_BFESS': 'FF85DF65CC7463F3726D5301B69C0672:FG=1',
    'PSTM': '1744882843',
    'BIDUPSID': '950D047CF79B4A0F8F86462CD08D849F',
    'ZFY': ':AYs:BOm:Ajfa1cQtiOrSJADVlDld3:BYmMcahDksItTkOQ:C',
    'H_PS_PSSID': '61027_62325_62485_62967_63042_63044_63140_63074_63189_63194_63210_63226_63242_63244_63249_63253',
    '__bid_n': '18c42450fcc02886ca93f5',
    'BDUSS': '3ZlcTY5VmdtR055LS0yWUZIekVwaXpQdlhhZTVWNkQ1RjJZd1Z2RjZlMnZKb0pvSVFBQUFBJCQAAAAAAAAAAAEAAABKXe14tuS25MCyxL625AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK-ZWmivmVpoa',
    'bdindexid': 'lbjajepvj48ik2npi9efsppm32',
    'Hm_lvt_d101ea4d2a5c67dab98251f0b5de24dc': '1750687271,1750768658',
    'HMACCOUNT': 'DDF927EE5DF25454',
    'SIGNIN_UC': '70a2711cf1d3d9b1a82d2f87d633bd8a05007811055iHW74BOJZpR8fIXeOGeBx5M6y7phE8fVUA6A5%2FT9V%2FlsHxmc8X4j0VNC%2F9LwP2zmQdfNMKxnxGOsso9i6z5EBqAppSnxsfJ24BKZ2HbQq2iyXFknWsLKsmgGjJw1B4gnKBPQaKQ17uqsRk7kRjIMxMQ9I09xx2H5mLprCONYZIbGfHaYp1BTvGG6rrGQtybXmNaMwxxsWVpk5FXOZ9eQ4K3Wkdor%2FZuxF6vZoZZboMBLW7wT1x8%2FnAf2M49uCYlG7sR%2B%2F2vpsj8pGF1p7tZvY9RSVz9Zuo7VoVT643%2FkQeIjx7VwkUgLo5BwXQ4wGzR60WWFDjO93A1KqcAW0Cufkg%3D%3D19042442273391681046897992923981',
    '__cas__st__212': 'bbc20157a0eb310bf75a06fe47852349e3fdc208669fbd29ee3ef0f2081a8a25ae8d802c8eff57ed1747ef5a',
    '__cas__id__212': '69563296',
    '__cas__rn__': '500781105',
    'CPTK_212': '1747583717',
    'CPID_212': '69563296',
    'RT': 'z=1&dm=baidu.com&si=454d90be-3dae-4ce7-84a2-ab2e9d648c5d&ss=mcbaf2i5&sl=0&tt=0&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf',
    'BDUSS_BFESS': '3ZlcTY5VmdtR055LS0yWUZIekVwaXpQdlhhZTVWNkQ1RjJZd1Z2RjZlMnZKb0pvSVFBQUFBJCQAAAAAAAAAAAEAAABKXe14tuS25MCyxL625AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK-ZWmivmVpoa',
    'Hm_lpvt_d101ea4d2a5c67dab98251f0b5de24dc': '1750816072',
    'ab_sr': '1.0.1_NDQ4MjFmZWIxYjFhNjAwYzk2NjM2YzZkYTc5ODk1MmM4YTA1Yjk2ZTgzNjE5OWQ1YzMwOGZiOGQ2OTUyODAzMjk5NjE5MDJiNzdkOTkxN2JlNTU5MDQ2MjY0NGZlZTFhMmI3N2E2ZjRlODhjZmY3OTQzZGY1YTRlYjMzYzUzYjgwODk3ZTg1MmE2OTdmZDY3YzQyN2NmZGNiNjk1MTdjZQ=='
}

#     'BAIDU_WISE_UID': 'wapp_1744869667916_527',
#     'BAIDUID': 'FF85DF65CC7463F3726D5301B69C0672:FG=1',
#     'BAIDUID_BFESS': 'FF85DF65CC7463F3726D5301B69C0672:FG=1',
#     'PSTM': '1744882843',
#     'BIDUPSID': '950D047CF79B4A0F8F86462CD08D849F',
#     'ZFY': ':AYs:BOm:Ajfa1cQtiOrSJADVlDld3:BYmMcahDksItTkOQ:C',
#     '__bid_n': '18c42450fcc02886ca93f5',
#     'BDUSS': '3ZlcTY5VmdtR055LS0yWUZIekVwaXpQdlhhZTVWNkQ1RjJZd1Z2RjZlMnZKb0pvSVFBQUFBJCQAAAAAAAAAAAEAAABKXe14tuS25MCyxL625AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK-ZWmivmVpoa',
#     'H_PS_PSSID': '62325_63140_63324_63401_63584_63638_63643_63647_63659_63724_63712_63749_63756',
#     'Hm_lvt_d101ea4d2a5c67dab98251f0b5de24dc': '1750687271,1750768658,1751079964,1751181661',
#     'HMACCOUNT': 'DDF927EE5DF25454',
#     'bdindexid': 'f66itdoq39iiem694ho44h70n3',
#     'SIGNIN_UC': '70a2711cf1d3d9b1a82d2f87d633bd8a05011941100edWg33s3DV8OV0CJlsjP0DBLlBTc0b5Jwg9dqdt5vVlB%2BsFyuefaEWS81mVoiy2BAKuTdFm%2BOcxSI7kjW9mmyi0kuPQ8NUMh1HwJd0wGsV4Y1Pnz1WD0PhkojzJXZI19rQUTGBrXRzP6705tEO3cTiVxdviICWVMnKOcZw6DUJmUo9FxgqK%2FqsZ%2BBQeHOClvb0hgJS%2FOgwGbDbDLlWxsm77HPeusF4P%2FydHB4KOn27CmvJMA2LuRZv2ZIR9G7rIYsJoOf5mRnIZzUZUg2mSf1PpfmVE4oMC%2B25%2F4GwPWi9gKLEvNu3hI466jMrNuwAkvezVMVZLDHPaabaauoUgBLQ%3D%3D01766774846724411156782136199821',
#     '__cas__rn__': '501194110',
#     '__cas__st__212': 'a7f09d59c3bc1a452c603a087d576a16f04a4b672d409f08bb0a3d40204c45fa5e4522bea1de0d302a1a38af',
#     '__cas__id__212': '69563296',
#     'CPTK_212': '552996471',
#     'CPID_212': '69563296',
#     'RT': '"z=1&dm=baidu.com&si=454d90be-3dae-4ce7-84a2-ab2e9d648c5d&ss=mchccgwg&sl=g&tt=mzh&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf"',
#     'Hm_lpvt_d101ea4d2a5c67dab98251f0b5de24dc': '1751182559',
#     'ab_sr': '1.0.1_NzNhOWYxMmI5MDFkMDBiMTVkYmRjMzVmNzI2OGRiZTRmOGUyMjFkZTRmZTc4NDY4N2NkZDA0ZTk2OGM3YTUyMzI0OGYxNzIwNDlkYWI0N2JmZTY4ZTZlZDY1NWNlMjEyMTY2ZGE3MmM0MTY0NTM3OTk3YzMyZjkxODRiY2RmZDBmZGRlOWU4MDY1YTA1MTk0MjVkYzc4MzJmN2QwNWYwOQ==',
#     'BDUSS_BFESS': '3ZlcTY5VmdtR055LS0yWUZIekVwaXpQdlhhZTVWNkQ1RjJZd1Z2RjZlMnZKb0pvSVFBQUFBJCQAAAAAAAAAAAEAAABKXe14tuS25MCyxL625AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK-ZWmivmVpoa',
# {
#     'BAIDUID': '6F035D091225E0FFE4908C90D70AD822:FG=1',
#     'BA_HECTOR': '0121a1258405a52h05a5i0052trm4s1k0bkat22',
#     'BDORZ': 'AE84CDB3A529C0F8A2B9DCDD1D18B695',
#     'bd_af': '1',
#     'SE_LAUNCH': '5%3A29086862_0%3A29086862',
#     'logTraceID': '1797801a3c600de65917ef65ef1d2f86191ae05fcafc7c7a4c',
#     'BAIDU_WISE_UID': 'wpass_1745211887278_498',
#     'HISTYPE': '464ab677cb50e66299b1173bfbfd30a8075da833',
#     'SAVEUSERID': 'a613a9378129c712e8ffef028cd945',
#     'UBI': 'fi_PncwhpxZ%7ETaJc5BhCCmgRHsX9%7EV0sQU0',
#     'HISTORY': '4ae42981f07603a8503cfba707cd2fd4a5184e',
#     'PTOKEN': '23f654ed75bbc71d23af80452168ecdd',
#     'BDUSS': '2RkMkl0RUMwNHh6a2R-RnlVaGFmZmV1c1Y5ZGd6TWxsdmMtQWctUW1TanZYaTFvRVFBQUFBJCQAAAAAAQAAAAEAAACyxBCXQVphODQ4ODE3AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAO~RBWjv0QVoR',
#     'STOKEN': 'eca8b22a9308cae99398c539b0b1435ab254ca1ecae722594bde0e96741bb12e',
#     '__bid_n': '19656ba005005766db9ac1',
#     'fuid': 'FOCoIC3q5fKa8fgJnwzbE3sZaS3poGTofPItBD67MTHOloTQtOTfZukshuG%2BjikL4W7tz5yLAvmohSU1nOBwSDdXRergGMxbYDe0QJOx3ig80a0mIC63O1c%2FBqEcMZVC5V%2FzNUpLEokpWzcno%2BKUGBuSZbHXdousNlXNZr5jO0AvJtn1O5lWzGMQkFhNOLYdX65B3ntaX4EpPKtgIsF42NLpjQDF22s1z8%2BSNqoNmkmDCTx%2BTKL6w8GdxcRcztzA0KCW4y3gL0%2Bx%2B9R3bd9LHOb679Knr40H9B6zovvywMHBzc2sZvrgJOXi%2FiDQUzufMzUuKkwELga8f2H51MsSNJR67GJOgKAN%2F9ZA0cyBytB6qEGLYOh%2FONfiFdHd%2BRk9HSUGGK9g6JxGFzohdyyVcZlPnmOSyBOCNOSiCV8knMk1slEN%2BViKJ9mQd1J%2FRTLpd1LLXXo2U70WwlfVbkbQ%2FNwWESDc3WjNykHQgmFW5sUV4uzjDKAi%2FqbTr2WGx2bN67l1jJiOBxk4GDIdx5%2FaJAUxvv4kVbE0agDQk2K%2FqEJvSCRemQSkhKLq1UeH6GxCJ%2BMAIYbPQxssj0AC629A2Yui9ATwOutSQ49JZmSIHAhS%2FGidIZLaWCI1kHGAr81p3o%2Fex%2B%2FK9iHJc3DGbpLMf46NrWXpzL26g%2FvLjjogtrUIsQ5pXWMOQaiSw2FG2fsHzUJ6aS6x2ARHpppRXfhHh4ZaJNSUKp1t%2FygYdhyiZtb0PJErm9NuhhgSVQWw3o94fvkJSdbeTSUCYUcSDfs1oaktJ7CISS0STF94GtUDhRi%2FtsJB9aics6wilyMAm769%2FlTRa%2BIffW9qYdS%2F8IMr41ftb3vGuZ5AMhJMrFU3OYFNetS6mrAjm2GHsp1aRoBwrXcL%2FjvKH252h3bbQIEd5KpCpLHE5%2F11gXBWFEw88CJ5Iw4KsvF9ewnNvSZYYkOfGEQw3OLo5dsSUeQDd6vDni1evF%2FM7yvmL%2BFUAwPmWZFbvNq69O2z3wBW%2BogxJUDy9IDhObhno4D7MBZG4B%2BpNlhGWn0jikQ5zzmAASlnix3V2XtmwNAzvtRZUfKm%2Fj5ohXGVaLqOQwr5UIY0Yb6SLXLM1qkKE39xuHQXz2y787L7W199bwgobYc9164V8Y6I40dDn9N%2F3gRsPisyHi6z8aphVNhJG%2F707P2GcCYlcR4%3D',
#     'rsv_i': '16efZWvLAx1SDzEXaXaNunrYPfgaoMB8iliJYjFt0e7JWkHEFYR7Gb9hpppESFGQ+ZsnhGwBQG+wRfHx1AZpZEuKQIUhAxU',
#     'H_WISE_SIDS': '110085_633614_644900_644372_645169_645434_648741_648987_649230_649350_649341_649589_649909_8000082_8000133_8000136_8000149_8000156_8000162_8000165_8000173_8000177_8000180_8000186_8000203',
#     'delPer': '0'
# }