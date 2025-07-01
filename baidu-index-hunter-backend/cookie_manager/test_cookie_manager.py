"""
测试Cookie管理器功能
"""
import sys
import os
import random
import json
from datetime import datetime, timedelta
from pathlib import Path
import time

# 添加项目根目录到路径，以便导入项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cookie_manager import CookieManager

class CookieManagerTester:
    """Cookie管理器测试类"""
    
    def __init__(self):
        """初始化测试环境"""
        self.cookie_manager = CookieManager()
        self.test_account_id = f"test_account_{int(time.time())}"
        
    def run_all_tests(self):
        """运行所有测试"""
        print("开始测试Cookie管理器...")
        
        # 获取现有数据
        self.test_get_all_cookies()
        
        # # 测试添加解析cookie
        # self.test_add_parsed_cookie()
        
        # # 测试随机选择账号并删除/恢复字段
        # self.test_update_random_cookie()

        # 测试临时封禁和解封账号
        # self.test_temporary_ban_account()
        
        # # 测试永久封禁和解封
        self.test_permanent_ban_account()
        
        print("所有测试完成!")
        
    # 测试通过
    def test_get_all_cookies(self):
        """测试获取所有可用cookie"""
        print("\n=== 测试获取所有可用cookie ===")
        cookies = self.cookie_manager.get_available_cookies()
        print(f"获取到 {len(cookies)} 个可用cookie字段")
        
        # 测试获取所有可用账号ID
        account_ids = self.cookie_manager.get_available_account_ids()
        print(f"获取到 {len(account_ids)} 个可用账号ID")
        
        if cookies:
            # 打印第一个cookie的部分信息
            first_cookie = cookies[0]
            print(f"示例cookie字段: ID={first_cookie['id']}, 账号={first_cookie['account_id']}, 字段名={first_cookie['cookie_name']}，字段值={first_cookie['cookie_value']}，是否可用={first_cookie['is_available']}，是否被永久封禁={first_cookie['is_permanently_banned']}，临时封禁到期时间={first_cookie['temp_ban_until']}")
            
        return cookies
    
    # 测试通过
    def test_add_parsed_cookie(self):
        """测试添加解析cookie"""
        print("\n=== 测试添加解析cookie ===")
        
        # 测试cookie字典
        test_cookie_dict = {
            "BAIDU_WISE_UID": "wapp_1744869667916_527",
            "BAIDUID": "FF85DF65CC7463F3726D5301B69C0672:FG=1",
            "BAIDUID_BFESS": "FF85DF65CC7463F3726D5301B69C0672:FG=1",
            "PSTM": "1744882843",
            "BIDUPSID": "950D047CF79B4A0F8F86462CD08D849F",
            "ZFY": ":AYs:BOm:Ajfa1cQtiOrSJADVlDld3:BYmMcahDksItTkOQ:C",
            "__bid_n": "18c42450fcc02886ca93f5",
            "BDUSS": "3ZlcTY5VmdtR055LS0yWUZIekVwaXpQdlhhZTVWNkQ1RjJZd1Z2RjZlMnZKb0pvSVFBQUFBJCQAAAAAAAAAAAEAAABKXe14tuS25MCyxL625AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK-ZWmivmVpoa",
            "Hm_lvt_d101ea4d2a5c67dab98251f0b5de24dc": "1751181661,1751210338,1751213710,1751243261",
            "HMACCOUNT": "DDF927EE5DF25454",
            "SIGNIN_UC": "70a2711cf1d3d9b1a82d2f87d633bd8a0501255709984FEi9UEKliGHWSHXZ6oYd17WpvF4UpTpi0S%2FMkYmfiNAqK1M0jX%2FRqCmmXdrDEKGvA1CsZHHN0J6ilBmnFop%2F8%2B6kq5c6KzFnXz9L69g0uZoezgZ760lQ3%2FUb20RzzXNbk81Z8UtRs%2FPC06mHQdR82YpdoLC1zwfBABKuYj%2BJSlme6%2FJz8fJh4BK9HFN2Wz3RmPvMQj1MCnGMm79Lwvycr04s7oj8%2FcIHSQ4uxrGwiuKRkD%2BW0QDFVw%2FJv4smgVX%2BEyECGZwW%2BO0NxOEr65Tck9T8YE1aDXFoucNxhXryU4iEwfAomNvsLSlXKVdvtppWhAXzpyghmbU5%2BSA%2BJUIw%3D%3D34813889920872661871379264310074",
            "__cas__rn__": "501255709",
            "__cas__st__212": "8667dbced52a16d95b022f15621d78910c7bb72005387e9d4326869b031a70d6907b3470b90ff2b24eeeb20d",
            "__cas__id__212": "69563296",
            "CPTK_212": "1532251641",
            "CPID_212": "69563296",
            "bdindexid": "42r0a9do4patuegrcfi2pcmkl7",
            "H_PS_PSSID": "62325_63140_63324_63401_63584_63638_63647_63659_63724_63712_63756_63814",
            "BA_HECTOR": "00002kah0k0k21802185ak0h0ga48m1k64l3825",
            "BDRCVFR[S4-dAuiWMmn]": "I67x6TjHwwYf0",
            "delPer": "0",
            "PSINO": "5",
            "BDORZ": "B490B5EBF6F3CD402E515D22BCDA1598",
            "ab_sr": "1.0.1_NjFhN2NhZjQ2YWI1OGEwZTZiZjlmMGJhNjc5M2IzOGNjYzRkYTY3NzkzMmVhOTk2ZmI1YWIyZDAyNDFiZTQ3NzAyNWM0YjY1YTg4MGRhYjdkNGI5Njk0ZmQyZmViOGUxZTU3Mjg4OWMwZDNiYTZmNDE1YTk0YzYwZTZkZWFiNmUwOGJmZTlkZjI3YWNjN2M5ZTYyMzYyZjJhMDVkOTBiMg==",
            "RT": "\"z=1&dm=baidu.com&si=454d90be-3dae-4ce7-84a2-ab2e9d648c5d&ss=mcj832d2&sl=0&tt=0&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf\"",
            "Hm_lpvt_d101ea4d2a5c67dab98251f0b5de24dc": "1751295960",
            "BDUSS_BFESS": "3ZlcTY5VmdtR055LS0yWUZIekVwaXpQdlhhZTVWNkQ1RjJZd1Z2RjZlMnZKb0pvSVFBQUFBJCQAAAAAAAAAAAEAAABKXe14tuS25MCyxL625AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK-ZWmivmVpoa"
        }
        
        # 使用特定的测试账号ID
        test_account_id = f"test_parse_{int(time.time())}"
        
        # 添加cookie字典
        result = self.cookie_manager.add_cookie(test_account_id, test_cookie_dict)
        print(f"添加解析cookie结果: {'成功' if result else '失败'}")
        
        # 检查是否添加成功
        added_cookies = self.cookie_manager.get_cookies_by_account_id(test_account_id)
        print(f"成功添加 {len(added_cookies)} 个cookie")
        
        # 清理测试数据
        self.cookie_manager.delete_by_account_id(test_account_id)
        print(f"清理测试账号 {test_account_id} 的数据")
        
    # 测试通过，可以根据cookie字段的id来更新
    def test_update_random_cookie(self):
        """测试随机选择账号并删除/恢复字段"""
        print("\n=== 测试随机更新cookie字段 ===")
        
        # 获取所有可用cookie
        all_cookies = self.cookie_manager.get_available_cookies()
        
        if not all_cookies:
            print("没有可用的cookie，跳过此测试")
            return
        
        # 随机选择一个cookie
        random_cookie = random.choice(all_cookies)
        cookie_id = random_cookie['id']
        account_id = random_cookie['account_id']
        cookie_name = random_cookie['cookie_name']
        original_value = random_cookie['cookie_value']
        
        print(f"随机选择的cookie: ID={cookie_id}, cookie名称 = {account_id},字段名={cookie_name}，原始字段值={original_value}")
        
        # 更新为新值
        new_value = f"test_value_{int(time.time())}"
        update_data = {'cookie_value': new_value}
        
        result = self.cookie_manager.update_cookie(cookie_id, update_data)
        print(f"更新cookie字段值结果: {'成功' if result else '失败'}")
        
        # 恢复原始值
        restore_data = {'cookie_value': original_value}
        result = self.cookie_manager.update_cookie(cookie_id, restore_data)
        print(f"恢复原始值结果: {'成功' if result else '失败'}")
   
    # 测试通过
    def test_temporary_ban_account(self):
        """测试临时封禁和解封账号"""
        print("\n=== 测试临时封禁和解封账号 ===")
        
        # 获取所有可用账号ID
        account_ids = self.cookie_manager.get_available_account_ids()
        
        if not account_ids:
            print("没有可用的账号，跳过此测试")
            return
        
        # 随机选择一个账号
        random_account_id = random.choice(account_ids)
        
        print(f"随机选择的账号: {random_account_id}")
        
        # 获取该账号的cookie字段数量
        cookies_before = self.cookie_manager.get_cookies_by_account_id(random_account_id)
        available_count_before = sum(1 for c in cookies_before if c['is_available'] == 1)
        print(f"封禁前账号有 {len(cookies_before)} 个cookie字段，其中 {available_count_before} 个可用")
        
        # 临时封禁30秒（为了测试方便，使用较短时间）
        ban_duration = 30  # 30秒
        banned_count = self.cookie_manager.ban_account_temporarily(random_account_id, ban_duration)
        print(f"临时封禁账号结果: 封禁了 {banned_count} 个cookie字段")
        
        # 验证封禁状态
        cookies_after_ban = self.cookie_manager.get_cookies_by_account_id(random_account_id)
        available_count_after_ban = sum(1 for c in cookies_after_ban if c['is_available'] == 1)
        print(f"封禁后账号有 {len(cookies_after_ban)} 个cookie字段，其中 {available_count_after_ban} 个可用")
        
        # 解封账号
        unbanned_count = self.cookie_manager.unban_account(random_account_id)
        print(f"解封账号结果: 解封了 {unbanned_count} 个cookie字段")
        
        # 验证解封状态
        cookies_after_unban = self.cookie_manager.get_cookies_by_account_id(random_account_id)
        available_count_after_unban = sum(1 for c in cookies_after_unban if c['is_available'] == 1)
        print(f"解封后账号有 {len(cookies_after_unban)} 个cookie字段，其中 {available_count_after_unban} 个可用")

    # 测试通过
    def test_permanent_ban_account(self):
        """测试永久封禁和强制解封账号"""
        print("\n=== 测试永久封禁和强制解封账号 ===")
        
        # 创建专门用于测试的账号
        test_ban_account_id = f"test_ban_{int(time.time())}"
        test_cookie = {
            'test_name_1': 'test_value_1',
            'test_name_2': 'test_value_2',
            'test_name_3': 'test_value_3'
        }
        
        # 添加测试cookie
        self.cookie_manager.add_cookie(test_ban_account_id, test_cookie)
        print(f"为测试创建账号 {test_ban_account_id} 并添加测试cookie")
        
        # 获取该账号的cookie字段数量
        cookies_before = self.cookie_manager.get_cookies_by_account_id(test_ban_account_id)
        print(f"封禁前账号有 {len(cookies_before)} 个cookie字段，全部可用")
        
        # 永久封禁
        banned_count = self.cookie_manager.ban_account_permanently(test_ban_account_id)
        print(f"永久封禁账号结果: 封禁了 {banned_count} 个cookie字段")
        
        # 验证封禁状态
        cookies_after_ban = self.cookie_manager.get_cookies_by_account_id(test_ban_account_id)
        available_count = sum(1 for c in cookies_after_ban if c['is_available'] == 1)
        permanently_banned_count = sum(1 for c in cookies_after_ban if c['is_permanently_banned'] == 1)
        print(f"封禁后账号有 {len(cookies_after_ban)} 个cookie字段，其中 {available_count} 个可用，{permanently_banned_count} 个被永久封禁")
        
        # 尝试普通解封（应该无效）
        unbanned_count = self.cookie_manager.unban_account(test_ban_account_id)
        print(f"尝试普通解封永久封禁的账号结果: 解封了 {unbanned_count} 个cookie字段")
        
        # 验证普通解封后的状态
        cookies_after_unban = self.cookie_manager.get_cookies_by_account_id(test_ban_account_id)
        available_count = sum(1 for c in cookies_after_unban if c['is_available'] == 1)
        permanently_banned_count = sum(1 for c in cookies_after_unban if c['is_permanently_banned'] == 1)
        print(f"普通解封后账号有 {len(cookies_after_unban)} 个cookie字段，其中 {available_count} 个可用，{permanently_banned_count} 个被永久封禁")
        
        # 强制解封
        force_unbanned_count = self.cookie_manager.force_unban_account(test_ban_account_id)
        print(f"强制解封账号结果: 解封了 {force_unbanned_count} 个cookie字段")
        
        # 验证强制解封后的状态
        cookies_after_force_unban = self.cookie_manager.get_cookies_by_account_id(test_ban_account_id)
        available_count = sum(1 for c in cookies_after_force_unban if c['is_available'] == 1)
        permanently_banned_count = sum(1 for c in cookies_after_force_unban if c['is_permanently_banned'] == 1)
        print(f"强制解封后账号有 {len(cookies_after_force_unban)} 个cookie字段，其中 {available_count} 个可用，{permanently_banned_count} 个被永久封禁")
        
        # 清理测试数据
        # self.cookie_manager.delete_by_account_id(test_ban_account_id)
        # print(f"清理测试账号 {test_ban_account_id} 的数据")
        
    def __del__(self):
        """清理测试资源"""
        if hasattr(self, 'cookie_manager'):
            # 确保删除测试账号的所有cookie
            self.cookie_manager.delete_by_account_id(self.test_account_id)
            self.cookie_manager.close()

if __name__ == "__main__":
    tester = CookieManagerTester()
    try:
        tester.run_all_tests()
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    finally:
        # 确保资源被释放
        del tester 