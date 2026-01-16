import requests
import requests

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://index.baidu.com/v2/main/index.html",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "sec-ch-ua": "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\""
}
cookies = {
    "BAIDUID_BFESS": "D658E3EEA8E772A6FF26A4B5FA6A5198:FG=1",
    "__bid_n": "19b8802b5f771847426ba3",
    "jsdk-uuid": "b415f00a-c996-469c-9cb0-5cab4861ae8c",
    "Hm_lvt_d101ea4d2a5c67dab98251f0b5de24dc": "1768223096",
    "HMACCOUNT": "15EA9A03083153E5",
    "ppfuid": "FOCoIC3q5fKa8fgJnwzbE0LGziLN3VHbX8wfShDP6RCsfXQp/69CStRUAcn/QmhIlFDxPrAc/s5tJmCocrihdwitHd04Lvs3Nfz26Zt2holplnIKVacidp8Sue4dMTyfg65BJnOFhn1HthtSiwtygiD7piS4vjG/W9dLb1VAdqPDGlvl3S9CENy8XO0gBHvcO0V6uxgO+hV7+7wZFfXG0MSpuMmh7GsZ4C7fF/kTgmsdW/YK/SYZe7YnMQd/OOgPfwxc7LdfzCcwgTd+DadaM2nsKti2mNb/G7SRM0aHJJrpJIFqcvNsRYzITz5PyOAD6RLDT+sXOPQ6ovNaw3n8P6JLwMdIdH+eEAlE3PHwsfIZaGhxes+nljx68Dx7ernR3BLhoNACSIWjkgKwIzw9ZXiuQ06o/GW4wOMPJdiyMW/DD4QcrrDKONyfTAB58zeZ2dM1L+ksxZx66zR7vnv9Q5cEGZJcFoYiDD8SdrjRC/0AC/csJ/Vjv98cvc9NJ/2+J3+7ZUtfiHWcG3HwQXTt4IyFZW/7aqNs9XtmFeTet5pZEUR6yjez8pz2f9Re1R81TWweIJ1usJbnJiy5Iz1I8YNmyXsWFMArDuoi7fy8VmKr4NFzxVt/uM6I33E97SU51kdSEYdnzasvmNMKwgvBxFUKd2tqtvCa7sbXngyliIqZNdmSpXsCWjhBnOJx3IxtjYqFI758qwnezxhZiYQI3CVaRMddwageZwkoKGRnQySFUJ4z9dat2SGu7jamJ+GKtIWE+2v/7UlY7UEilXLVMcBSzQz7DvZmaDuSxJ3O265ivp1XmY/22FG3DNJSGqSFtRW1qMDSW4ctA6tWxe43W/T89HeLT1K4XNkmQkEoTcyfDX5iOsrasFocfPG0bRL+L3mWxdJ9pry4tTiAJxoX+QuOtuaTP81PXGjx/omkrurC+XBKAtjZANFKiCi9lU30XmOBp90ufa8q5fiybUPk6HXsR2R4RUkMFzFu4uek8JZtnMbokCWA+7pFeUspn1TxBphe+V4Fu14ttSLk2gIAKE/mhl+gJ6goq69QQA9ddM9WM7RNOLSxWoVJ0b4YXKLTfCWubfAJE3xCxaFPXSlckvRGFwtNqAOfFq4X1+WdXCL0BvZozJbj5gfVVlYhSFve0u80c9MeQcVKn6OT+e9IiqbZApjp5oasaKfm1YDpXXq6oW4FLPwjQp97RBnCTk5BbH8B3Xaw7bVLl7NdVFJKBfNDYYDl6HxqJXScM4aa1+GJg2NuzY3E/RpwCACk13R7",
    "SIGNIN_UC": "70a2711cf1d3d9b1a82d2f87d633bd8a05182356200n8Xa%2BkEFw%2F9%2FYx3kQf%2FXUx9Wchv50pKVvtR9FFlwvKcIgo69qu93E7VKVyLp3fEKJ7ES%2FR8u4qLZ7x7tp8di%2FZf18RPuvwi0OHO3QPe6ld1XjBdFfqifIIWAKSG2UYMF2mm0C0MWZ7e51KpGYgxFNFQtJkj%2FfUJYltJoZEtPhh79BZlgeySncyOvl7ym4s4Z9PAkKnk150JoA9egCYONmB1vwixnuDhlJ9%2FpUQbVaTlZO3vfBLQu4y5A8d2HV5EO8QWAyz9EJUurIamw7ItIvQ%3D%3D88978474898801067616575985830396",
    "__cas__rn__": "518235620",
    "BDUSS": "U1heFFnbmJQb01jZnJoTjQ1TEl-TGh-eVYzbWswUm52ajduRktCeElHakVmb3hwSVFBQUFBJCQAAAAAAQAAAAEAAACSeU9mTHVja19mZjA4MTAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMTxZGnE8WRpe",
    "__cas__st__212": "60de707e667228432cd7b512c0ec237bd9769d4bd4db057f17f5e373b5f615d4ff5713e02a4d86033330f0e9",
    "__cas__id__212": "69553869",
    "CPTK_212": "2135782210",
    "CPID_212": "69553869",
    "Hm_lpvt_d101ea4d2a5c67dab98251f0b5de24dc": "1768223174",
    "Hm_up_d101ea4d2a5c67dab98251f0b5de24dc": "%7B%22uid_%22%3A%7B%22value%22%3A%226011451794%22%2C%22scope%22%3A1%7D%7D",
    "ab_sr": "1.0.1_NzJiY2FmYzI0OWU4OWVhYjgzZWNjMjcxMjY0ZGVjZDA1NWExODliMGM2MzZlOTdkMjUyNThkMTYzNDJmNWY3MDFlMzEzMWIzZmY5MWYyZTliYTRmODQ1Njg3ZGFmNmQyMjhmN2RhZDFmNThiZmU5OTVkNDYxNmE0NzhmYmRmMjIwOGFjM2RiMGQyMzQxNWZmYzA4MTczOGQxNWNkODY4Ng==",
    "BDUSS_BFESS": "U1heFFnbmJQb01jZnJoTjQ1TEl-TGh-eVYzbWswUm52ajduRktCeElHakVmb3hwSVFBQUFBJCQAAAAAAQAAAAEAAACSeU9mTHVja19mZjA4MTAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMTxZGnE8WRpe",
    "bdindexid": "3eo1rpvrfb5p9a42ck8e3nk4f7",
    "RT": "\"z=1&dm=baidu.com&si=9f0a8178-99ee-438a-8de7-d74859b355dc&ss=mkb6dq3m&sl=3&tt=4yh&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ul=1y6&hd=1iqs\""
}
# 解密算法
def decrypt(t, e):
    if not t:
        return ""
    i = list(t)
    n = list(e)
    a = {}
    r = []
    
    # 构建映射字典
    for A in range(len(i) // 2):
        a[i[A]] = i[len(i) // 2 + A]
    
    # 根据映射解密数据
    for o in range(len(n)):
        r.append(a[n[o]])
    
    return ''.join(r)



data ={
    "status": 0,
    "data": {
        "userIndexes": [
            {
                "word": [
                    {
                        "name": "汽车",
                        "wordType": 1
                    }
                ],
                "all": {
                    "startDate": "2025-12-13",
                    "endDate": "2026-01-11",
                    "data": "N.-CZNXNXZNXk.ZNkNjZj-5XZkXkwZCCjNZkXwNZkX-5ZCNN-ZCwN5Z5X.jZ5-5NZ5w55Z5wCXZ-llXlZ-.-CjZ-lwjlZ-l5-NZ-.C5.Z-lw.jZ-.-kjZ-ll.jZ-lCl.Z---kjZ-XCj5ZNjXNZk..NZCj.kZkXww"
                },
                "pc": {
                    "startDate": "2025-12-13",
                    "endDate": "2026-01-11",
                    "data": "kCCZCwwZ5jwZ55CZ5NjZ5j5Z5jlZkljZk.XZ5j.Z5NXZ5NkZ5jXZ5CCZCN5ZCkjZ5k.Z5kCZ5C-ZCXkZk..ZkXCZ5j5Z5j5Z5CCZ5NXZ5kjZ5k-ZCNkZCCk"
                },
                "wise": {
                    "startDate": "2025-12-13",
                    "endDate": "2026-01-11",
                    "data": "jNNXZjkN-Zj-5CZjjwlZk.XCZC-w-Z.jXkZCkN-ZCC55Z.wX5ZC-X5ZN-j-ZN.lNZ5-CCZ5CjlZ--NCjZ-llw.Z-l-X5Z--wNjZ-.XN5Z-lCX.Z-ljklZ--.j5Z--kkkZ-X.-lZwkw5ZjNk-ZCC5jZC-jXZCjkC"
                },
                "type": "day"
            }
        ],
        "generalRatio": [
            {
                "word": [
                    {
                        "name": "汽车",
                        "wordType": 1
                    }
                ],
                "all": {
                    "avg": 8613,
                    "yoy": 33,
                    "qoq": -1
                },
                "pc": {
                    "avg": 725,
                    "yoy": -33,
                    "qoq": -8
                },
                "wise": {
                    "avg": 7887,
                    "yoy": 47,
                    "qoq": -1
                }
            }
        ],
        "uniqid": "ceb84972c7bb306c29014d24cf98c34a"
    },
    "logid": 2888691570,
    "message": 0
}
# 打印响应内容，查看实际数据结构
print("响应数据:", data)

# 检查数据结构并安全获取数据
if isinstance(data, dict) and 'data' in data and isinstance(data['data'], dict):
    # 获取解密密钥
    uniqid = data['data']['uniqid']
    print(uniqid)
    params = {
        'uniqid': uniqid,
    }
    url = "https://index.baidu.com/Interface/ptbk"
    response = response = requests.get(url, headers=headers, cookies=cookies, params=params)
    print(response.json())
    key = response.json()['data']
    
    # 获取用户指数数据并解密所有关键词的数据
    if 'userIndexes' in data['data'] and isinstance(data['data']['userIndexes'], list):
        print("\n解密所有关键词的指数数据:")
        for index, keyword_data in enumerate(data['data']['userIndexes']):
            # 获取关键词名称
            keyword_name = keyword_data.get('word', [{}])[0].get('name', f'关键词{index+1}')
            
            # 获取各平台数据
            all_data = keyword_data.get('all', {}).get('data', '')
            pc_data = keyword_data.get('pc', {}).get('data', '')
            wise_data = keyword_data.get('wise', {}).get('data', '')
            
            # 解密数据
            if all_data:
                decrypted_all = decrypt(key, all_data)
                print(f"\n关键词 '{keyword_name}' 的整体指数数据:")
                print(decrypted_all)
            
            if pc_data and pc_data != all_data:  # 避免重复打印相同数据
                decrypted_pc = decrypt(key, pc_data)
                print(f"\n关键词 '{keyword_name}' 的PC指数数据:")
                print(decrypted_pc)
            
            if wise_data:
                decrypted_wise = decrypt(key, wise_data)
                print(f"\n关键词 '{keyword_name}' 的移动指数数据:")
                print(decrypted_wise)
    else:
        print("无法获取userIndexes数据")
else:
    print("响应数据格式不正确")
