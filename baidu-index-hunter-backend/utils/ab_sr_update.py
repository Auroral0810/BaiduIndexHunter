import requests
import json
import execjs


headers = {
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "text/plain;charset=UTF-8",
    "Origin": "https://index.baidu.com",
    "Pragma": "no-cache",
    "Referer": "https://index.baidu.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\""
}
cookies = {
    'BAIDU_WISE_UID': 'wapp_1744869667916_527',
    'BAIDUID': 'FF85DF65CC7463F3726D5301B69C0672:FG=1',
    'BAIDUID_BFESS': 'FF85DF65CC7463F3726D5301B69C0672:FG=1',
    'PSTM': '1744882843',
    'BIDUPSID': '950D047CF79B4A0F8F86462CD08D849F',
    'ZFY': ':AYs:BOm:Ajfa1cQtiOrSJADVlDld3:BYmMcahDksItTkOQ:C',
    '__bid_n': '18c42450fcc02886ca93f5',
    'BDUSS': '3ZlcTY5VmdtR055LS0yWUZIekVwaXpQdlhhZTVWNkQ1RjJZd1Z2RjZlMnZKb0pvSVFBQUFBJCQAAAAAAAAAAAEAAABKXe14tuS25MCyxL625AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK-ZWmivmVpoa',
    'H_PS_PSSID': '62325_63140_63324_63401_63584_63638_63643_63647_63659_63724_63712_63749_63756',
    'Hm_lvt_d101ea4d2a5c67dab98251f0b5de24dc': '1751181661,1751210338,1751213710,1751243261',
    'HMACCOUNT': 'DDF927EE5DF25454',
    'SIGNIN_UC': '70a2711cf1d3d9b1a82d2f87d633bd8a0501255709984FEi9UEKliGHWSHXZ6oYd17WpvF4UpTpi0S%2FMkYmfiNAqK1M0jX%2FRqCmmXdrDEKGvA1CsZHHN0J6ilBmnFop%2F8%2B6kq5c6KzFnXz9L69g0uZoezgZ760lQ3%2FUb20RzzXNbk81Z8UtRs%2FPC06mHQdR82YpdoLC1zwfBABKuYj%2BJSlme6%2FJz8fJh4BK9HFN2Wz3RmPvMQj1MCnGMm79Lwvycr04s7oj8%2FcIHSQ4uxrGwiuKRkD%2BW0QDFVw%2FJv4smgVX%2BEyECGZwW%2BO0NxOEr65Tck9T8YE1aDXFoucNxhXryU4iEwfAomNvsLSlXKVdvtppWhAXzpyghmbU5%2BSA%2BJUIw%3D%3D34813889920872661871379264310074',
    '__cas__rn__': '501255709',
    '__cas__st__212': '8667dbced52a16d95b022f15621d78910c7bb72005387e9d4326869b031a70d6907b3470b90ff2b24eeeb20d',
    '__cas__id__212': '69563296',
    'CPTK_212': '1532251641',
    'CPID_212': '69563296',
    'bdindexid': '42r0a9do4patuegrcfi2pcmkl7',
    'RT': '"z=1&dm=baidu.com&si=454d90be-3dae-4ce7-84a2-ab2e9d648c5d&ss=mcis9mum&sl=7&tt=5lm&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf"',
    'Hm_lpvt_d101ea4d2a5c67dab98251f0b5de24dc': '1751270136',
    # 'ab_sr': '1.0.1_MGEzOGQ3MjY3MjNkYmE3OTk0ZGEzNDJkNjhmZGU1MTZjZjc1OWMzNzBkODA0NDhkNWUxNGM2MTQzNDhhNzVhNjgzYjQ4ODQxOGY5MmY4NDYxYTY1YjJjYjNlNDZkYjkyMTJmMTNlN2U0NjIzZGJlMWI1MDI4OWEyMjExODIwNzAxYTQ2MzAxODhjMzBhOTA0ZTE3NGM4ZTNjY2UyNjVkMQ==',
    'BDUSS_BFESS': '3ZlcTY5VmdtR055LS0yWUZIekVwaXpQdlhhZTVWNkQ1RjJZd1Z2RjZlMnZKb0pvSVFBQUFBJCQAAAAAAAAAAAEAAABKXe14tuS25MCyxL625AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK-ZWmivmVpoa',
    }
url = "https://miao.baidu.com/abdr"
params = {
    "_o": "https://index.baidu.com"
}
with open('/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/utils/ab_sr.js', 'r') as f:
    js_code = f.read()

# 编译JS代码
ctx = execjs.compile(js_code)
data_js = ctx.call('get_data')
# print(data_js)
data_obj = json.loads(data_js)

# 使用从JS获取的数据构建请求体
data = {
    "data": data_obj["data"],
    "key_id": data_obj["key_id"],
    "enc": data_obj["enc"]
}
# 将数据转换为JSON字符串，不包含空格
data_json = json.dumps(data, separators=(',', ':'))

# 发送请求
response = requests.post(url, headers=headers, cookies=cookies, params=params, data=data_json)

print(response.cookies.get('ab_sr'))