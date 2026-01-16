import requests
import json

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8",
    "Cache-Control": "no-cache",
    "Cipher-Text": "1768190695911_1768224157075_qkf0ehcYqvy8SZitcjv+5Y7suCdvMDopjc+sMGP+9dmhFkNMDsR4zbjy5wsLp4RL0hchx+v2NbVHwCQaDxnh/j/kcHbaAKSlWDJUfhQIW56ZkXmTFfhVhUEH065oJkUQcewzB5BQAPjkGKBQfFJwS63RCW/j1SxXwi+MtRQWQQ3nTn1wlR46t5fubzQCGeSg6hfqqomCjQv2HM375ZvhcL19UKuolhGOHHiS0okrU+E8KzbMjackQZe1WoDjG1aBKiXw1a3OkWGycJAFptxxO/oPjYrDk0HxgZ1kOFBkL+50hjupy4MH3ORXARGNAl9hEUiwux9EH7sfwmJ37yt9IN0Gr1I132UWzL5VfwmE8PapTFTY3fCGXdYGOzULkbhBfV5MJG1HOSmmAOHXjPo60fnyqbqeN2DzoUf8NE4gJ2QIRc3dHq4QfhOq51y865BIejo4l8vg7XWS3RCox5ZbWqzLTX6U7OETwD5Eeww+KT8=",
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
    "bdindexid": "3eo1rpvrfb5p9a42ck8e3nk4f7",
    "BDUSS_BFESS": "U1heFFnbmJQb01jZnJoTjQ1TEl-TGh-eVYzbWswUm52ajduRktCeElHakVmb3hwSVFBQUFBJCQAAAAAAQAAAAEAAACSeU9mTHVja19mZjA4MTAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMTxZGnE8WRpe",
    "RT": "\"z=1&dm=baidu.com&si=9f0a8178-99ee-438a-8de7-d74859b355dc&ss=mkb6dq3m&sl=3&tt=4mf&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ul=1y6&hd=1iqs\""
}
# 构造参数
import json

# 使用JSON格式构造word参数
word_list = [
    [{"name": "三公经费", "wordType": 1}],
    [{"name": "决算", "wordType": 1}],
    [{"name": "小金库", "wordType": 1}],
    [{"name": "政府采购", "wordType": 1}],
    [{"name": "政府预算", "wordType": 1}],
]
# 将word_list转换为JSON字符串
word_json = json.dumps(word_list, ensure_ascii=False)

params = {
    "area": "0",
    "word": word_json,
    "startDate": "2011-01-01",
    "endDate": "2011-12-31"
}

# 构造URL
import urllib.parse
encoded_word = urllib.parse.quote(params["word"])
url = f"https://index.baidu.com/api/SearchApi/index?area={params['area']}&word={encoded_word}&startDate={params['startDate']}&endDate={params['endDate']}"
print(url)

# 发送请求
response = requests.get(url, headers=headers, cookies=cookies)

# 打印响应结果
result = response.json()
print(result)

# 统计关键词数量
if result.get('status') == 0 and 'data' in result and 'userIndexes' in result['data']:
    keyword_count = len(result['data']['userIndexes'])
    print(f"关键词总数: {keyword_count}")
    
    # 打印每个关键词的名称
    print("\n关键词列表:")
    for i, user_index in enumerate(result['data']['userIndexes']):
        if 'word' in user_index and len(user_index['word']) > 0:
            keyword_name = user_index['word'][0].get('name', '未知')
            print(f"{i+1}. {keyword_name}")
else:
    print("未能获取到关键词数据")