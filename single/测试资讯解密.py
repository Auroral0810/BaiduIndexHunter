import requests


headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8",
    "Cache-Control": "no-cache",
    "Cipher-Text": "1768709117972_1768759008343_JfPQnTqisIQ3CStswuNnHbEz9v76VJsqoobybXGjrUfjGaNTw3/uPxxBnLxToErT9IPzDqQ0YqFRgVsUgLy6QyKq5RH2hDuNWcXpPQtyVnPa2ZJuVPkPE8wrX+NbF30Cx341BJ4j/OLc6/9JuRxXddQtwiDX1NVOMH2A+rwr+FaOzP7pj/0na/cxOqpyfeAWDS3k7U5qwUe0w8ewi/YzIUsgbvHxf63AYGAh0dH9mAXJL2lmqnBLI0Oi8n7lripOQFZgkGyUb7Xd7l1z+Ab8KzII68UomPZ10s4QC0fVlTcWUl+3SX783bz+hsYyeTrFPwRCpBF7KZQtUtX5GrgVX4kq0N5ihOJaD1TRe2qvvpSuD5kaqWi2nT9WxCRVJ98BneW8NiV6yQCIIPaOSGL91Cn55td4MwTAVXdhU+9MryCfhm0DzYfnRn8moEtUW5wH",
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
    "BDUSS": "U1heFFnbmJQb01jZnJoTjQ1TEl-TGh-eVYzbWswUm52ajduRktCeElHakVmb3hwSVFBQUFBJCQAAAAAAQAAAAEAAACSeU9mTHVja19mZjA4MTAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMTxZGnE8WRpe",
    "Hm_up_d101ea4d2a5c67dab98251f0b5de24dc": "%7B%22uid_%22%3A%7B%22value%22%3A%226011451794%22%2C%22scope%22%3A1%7D%7D",
    "BIDUPSID": "D658E3EEA8E772A6FF26A4B5FA6A5198",
    "PSTM": "1768624123",
    "H_PS_PSSID": "63148_64006_66676_66846_66937_67045_67086_67121_67127_67146_66949_67154_67160_67182_67226_67209_67227_67239_67262_67231_67233_67244_67268_67252_67292_67313_67318_67316_67314_67323_67321_67304",
    "delPer": "0",
    "PSINO": "3",
    "ZFY": "o5AuKbeh:AeXSCMm4plskvnMJ4exwuGEuxpeNnZ4HqQI:C",
    "H_WISE_SIDS": "63148_64006_66676_66846_66937_67045_67086_67121_67127_67146_66949_67154_67160_67182_67226_67209_67227_67239_67262_67231_67233_67244_67268_67252_67292_67313_67318_67316_67314_67323_67321_67304",
    "log_first_time": "1768625632317",
    "log_last_time": "1768626769558",
    "H_WISE_SIDS_BFESS": "63148_64006_66676_66846_66937_67045_67086_67121_67127_67146_66949_67154_67160_67182_67226_67209_67227_67239_67262_67231_67233_67244_67268_67252_67292_67313_67318_67316_67314_67323_67321_67304",
    "bdindexid": "qgf9l8cot1edv6lh10ku74ca56",
    "SIGNIN_UC": "70a2711cf1d3d9b1a82d2f87d633bd8a05187274322VysNsAOR7n954ySDgJVPZYVNUDcW4l9TWZcminS9a89cbB1kERVlOfLllmIeTI9My5liHifvYT9gAFPu37tukxYf27g0oNEU7dpLoRQ%2BYCZKwJEM%2BQ301jPcRy8ax5jcf11ZqrbUa9DtmVEHi%2FoJVmMWXfLvEYoUnSEtIGZRW5vHR7Mn5epSr9EXNVUkmvego0r6R0dZ347UohCyOSzKrWZ7D7H%2FPs0tSKuuwDOx%2F%2F9ycpeQ6JG70TRx7ogYKoadwr7ouk9YrItJh6CfembT%2Fg%3D%3D41147885607113599363057325051142",
    "__cas__rn__": "518727432",
    "__cas__st__212": "60de707e667228432cd7b512c0ec237bd9769d4bd4db057f17f5e373b5f615d4ff5713e02a4d86033330f0e9",
    "__cas__id__212": "69553869",
    "CPTK_212": "2135782210",
    "CPID_212": "69553869",
    "Hm_lpvt_d101ea4d2a5c67dab98251f0b5de24dc": "1768758136",
    "ab_sr": "1.0.1_ZTc3MDRlMmRjNWQwYjY2MzVmNGI0MmMxMmEyZWVhOTY3NWI3OGFkNTcyMjBlZTgxMDVkMmY2MTQxODAxYjRiMzgyMjZlMDBmY2UwNDkzOWMwYTEzMTFkY2I4OThhNzM5MGVmOTI4MjQ2YjViMzEzM2UxYjQ0NWJlY2JjYmVhZjUwZWY0ZjBhMWQzOTFmNGRlMzFmMjRhNjgxNTAyYjRkNg==",
    "BDUSS_BFESS": "U1heFFnbmJQb01jZnJoTjQ1TEl-TGh-eVYzbWswUm52ajduRktCeElHakVmb3hwSVFBQUFBJCQAAAAAAQAAAAEAAACSeU9mTHVja19mZjA4MTAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMTxZGnE8WRpe",
    "RT": "\"z=1&dm=baidu.com&si=9f0a8178-99ee-438a-8de7-d74859b355dc&ss=mkhu19uc&sl=ok&tt=3dc6&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ld=z7kx&nu=2ua2g7gp&cl=10m0j&ul=10m0q&hd=26w1no\""
}

url = "https://index.baidu.com/api/FeedSearchApi/getFeedIndex"
params = {
    "area": "343",  # 343 对应普洱地区
    "word": "[[{\"name\":\"普洱\",\"wordType\":1}],[{\"name\":\"手机\",\"wordType\":1}]]",  # 多个关键词查询
    "startDate": "2017-07-03",
    "endDate": "2026-01-17"
}
response = requests.get(url, headers=headers, cookies=cookies, params=params)

# 解密算法说明：
# 百度指数API返回的数据是加密的，需要通过ptbk接口获取解密密钥
# 参数 t (密钥): 由两部分组成，前半部分是原始字符，后半部分是映射字符
# 参数 e (加密数据): 需要解密的数据字符串
# 解密原理: 将密钥前半部分的字符映射到后半部分对应位置的字符，然后用此映射表解密数据
def decrypt(t, e):
    if not t:
        return ""
    i = list(t)
    n = list(e)
    a = {}
    r = []
    
    # 构建映射字典：密钥前半部分字符 -> 后半部分对应字符
    for A in range(len(i) // 2):
        a[i[A]] = i[len(i) // 2 + A]
    
    # 根据映射解密数据
    for o in range(len(n)):
        r.append(a[n[o]])
    
    return ''.join(r)


data = response.json()
# 打印响应内容，查看实际数据结构
print("响应数据:", data)

# 检查数据结构并安全获取数据
# 注意：FeedSearchApi/getFeedIndex 返回的数据结构与 SearchApi/index 不同
# 它返回的是 data.index[].data 格式，数据已经在 index 数组中
if isinstance(data, dict) and 'data' in data and isinstance(data['data'], dict):
    # 获取 uniqid 用于后续解密
    uniqid = data['data']['uniqid']
    
    # 获取解密密钥
    key_params = {
        'uniqid': uniqid,
    }
    key_response = requests.get('https://index.baidu.com/Interface/ptbk', params=key_params, cookies=cookies, headers=headers)
    key = key_response.json()['data']
    print("解密密钥:", key)
    
    # 获取 index 数据（资讯指数的数据在 index 数组中）
    if 'index' in data['data'] and isinstance(data['data']['index'], list) and len(data['data']['index']) > 0:
        # 遍历所有关键词的数据
        for idx, index_data in enumerate(data['data']['index']):
            # 获取关键词名称
            key_info = index_data.get('key', [])
            keyword_name = key_info[0].get('name', f'关键词{idx+1}') if key_info else f'关键词{idx+1}'
            
            encrypted_data = index_data.get('data', '')
            startDate = index_data.get('startDate', '')
            endDate = index_data.get('endDate', '')
            data_type = index_data.get('type', '')  # week 表示按周统计
            
            # 获取 generalRatio（在 index 数组的每个元素中）
            generalRatio = index_data.get('generalRatio', {})
            generalRatio_avg = generalRatio.get('avg', 0)
            generalRatio_yoy = generalRatio.get('yoy', '-')
            generalRatio_qoq = generalRatio.get('qoq', '-')
            
            print(f"\n========== 关键词: {keyword_name} ==========")
            print(f"数据类型: {data_type}")
            print(f"日期范围: {startDate} 到 {endDate}")
            print(f"日均值: {generalRatio_avg}, 同比: {generalRatio_yoy}, 环比: {generalRatio_qoq}")
            
            # 解密趋势数据
            if encrypted_data:
                decrypted_data = decrypt(key, encrypted_data)
                print(f"解密后的数据: {decrypted_data}")
                
                # 将解密后的数据按逗号分隔（如果有的话）
                if ',' in decrypted_data:
                    data_list = decrypted_data.split(',')
                    print(f"数据点数量: {len(data_list)}")
                    print(f"前10个数据点: {data_list[:10]}")
                else:
                    print("数据格式可能不包含逗号分隔符")
            else:
                print("没有加密数据需要解密")
    else:
        print("无法获取index数据")
else:
    print("响应数据格式不正确")
