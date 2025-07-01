"""
API测试脚本，用于测试Cookie管理API
"""
import requests
import json
import time

# API基础URL
BASE_URL = 'http://localhost:5000/api/admin/cookie'

def print_response(response):
    """打印响应内容"""
    try:
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应内容: {json.dumps(data, ensure_ascii=False, indent=2)}")
        print("-" * 50)
        return data
    except Exception as e:
        print(f"解析响应失败: {e}")
        print(f"原始响应: {response.text}")
        print("-" * 50)
        return None

def test_list_cookies():
    """测试获取Cookie列表"""
    print("\n测试获取Cookie列表")
    # 获取所有可用的Cookie
    response = requests.get(f"{BASE_URL}/list")
    data = print_response(response)
    
    # 获取所有Cookie（包括不可用的）
    response = requests.get(f"{BASE_URL}/list?available_only=false")
    print_response(response)
    
    # 如果有数据，获取第一个账号的Cookie
    if data and data.get('data') and len(data['data']) > 0:
        account_id = data['data'][0]['account_id']
        print(f"\n获取账号 {account_id} 的Cookie")
        response = requests.get(f"{BASE_URL}/list?account_id={account_id}")
        print_response(response)

def test_list_accounts():
    """测试获取账号列表"""
    print("\n测试获取账号列表")
    response = requests.get(f"{BASE_URL}/accounts")
    print_response(response)

def test_add_cookie():
    """测试添加Cookie"""
    print("\n测试添加Cookie")
    # 创建测试数据
    test_data = {
        "account_id": "test_account_" + str(int(time.time())),
        "cookie_data": {
            "BDUSS": "test_bduss_value",
            "PTOKEN": "test_ptoken_value",
            "STOKEN": "test_stoken_value"
        },
        "expire_days": 30
    }
    
    response = requests.post(f"{BASE_URL}/add", json=test_data)
    data = print_response(response)
    
    return test_data["account_id"]

def test_update_cookie(cookie_id):
    """测试更新Cookie"""
    print(f"\n测试更新Cookie {cookie_id}")
    update_data = {
        "cookie_value": "updated_value_" + str(int(time.time()))
    }
    
    response = requests.put(f"{BASE_URL}/update/{cookie_id}", json=update_data)
    print_response(response)

def test_ban_temporarily(account_id):
    """测试临时封禁账号"""
    print(f"\n测试临时封禁账号 {account_id}")
    ban_data = {
        "duration_seconds": 60  # 封禁60秒
    }
    
    response = requests.post(f"{BASE_URL}/ban/temporary/{account_id}", json=ban_data)
    print_response(response)

def test_unban(account_id):
    """测试解封账号"""
    print(f"\n测试解封账号 {account_id}")
    response = requests.post(f"{BASE_URL}/unban/{account_id}")
    print_response(response)

def test_ban_permanently(account_id):
    """测试永久封禁账号"""
    print(f"\n测试永久封禁账号 {account_id}")
    response = requests.post(f"{BASE_URL}/ban/permanent/{account_id}")
    print_response(response)

def test_force_unban(account_id):
    """测试强制解封账号"""
    print(f"\n测试强制解封账号 {account_id}")
    response = requests.post(f"{BASE_URL}/force-unban/{account_id}")
    print_response(response)

def test_update_status():
    """测试更新Cookie状态"""
    print("\n测试更新Cookie状态")
    response = requests.post(f"{BASE_URL}/update-status")
    print_response(response)

def test_cleanup_expired():
    """测试清理过期Cookie"""
    print("\n测试清理过期Cookie")
    response = requests.post(f"{BASE_URL}/cleanup-expired")
    print_response(response)

def test_update_account_id(old_account_id):
    """测试更新账号ID"""
    print(f"\n测试更新账号ID {old_account_id}")
    new_account_id = "new_" + old_account_id
    update_data = {
        "new_account_id": new_account_id
    }
    
    response = requests.put(f"{BASE_URL}/update-account/{old_account_id}", json=update_data)
    print_response(response)
    
    return new_account_id

def test_delete_account(account_id):
    """测试删除账号"""
    print(f"\n测试删除账号 {account_id}")
    response = requests.delete(f"{BASE_URL}/delete/{account_id}")
    print_response(response)

def run_all_tests():
    """运行所有测试"""
    # 先获取现有数据
    test_list_cookies()
    test_list_accounts()
    
    # 添加新Cookie
    account_id = test_add_cookie()
    
    # 获取该账号的Cookie
    print(f"\n获取新添加账号 {account_id} 的Cookie")
    response = requests.get(f"{BASE_URL}/list?account_id={account_id}")
    data = print_response(response)
    
    # 如果获取到Cookie，测试更新操作
    if data and data.get('data') and len(data['data']) > 0:
        cookie_id = data['data'][0]['id']
        test_update_cookie(cookie_id)
    
    # 测试封禁和解封操作
    test_ban_temporarily(account_id)
    time.sleep(2)  # 等待2秒
    test_unban(account_id)
    test_ban_permanently(account_id)
    test_force_unban(account_id)
    
    # 测试状态更新和清理
    test_update_status()
    test_cleanup_expired()
    
    # 测试更新账号ID
    new_account_id = test_update_account_id(account_id)
    
    # 测试删除操作
    test_delete_account(new_account_id)

if __name__ == "__main__":
    run_all_tests() 