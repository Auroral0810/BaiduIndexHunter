import requests


headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://index.baidu.com/v2/main/index.html",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\""
}
cookies = {
    "BAIDUID": "FF85DF65CC7463F3726D5301B69C0672:FG=1",
    "PSTM": "1744882843",
    "BIDUPSID": "950D047CF79B4A0F8F86462CD08D849F",
    "BDUSS": "3ZlcTY5VmdtR055LS0yWUZIekVwaXpQdlhhZTVWNkQ1RjJZd1Z2RjZlMnZKb0pvSVFBQUFBJCQAAAAAAAAAAAEAAABKXe14tuS25MCyxL625AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK-ZWmivmVpoa",
    "H_PS_PSSID": "62325_63140_63324_63724_63712_63881_63913_63897_63952_63947_63961_63962_63979_63995_63274_64010_64014_64027",
    "BDORZ": "B490B5EBF6F3CD402E515D22BCDA1598",
    "BAIDUID_BFESS": "FF85DF65CC7463F3726D5301B69C0672:FG=1",
    "Hm_lvt_d101ea4d2a5c67dab98251f0b5de24dc": "1751213710,1751243261,1751388120,1752409661",
    "HMACCOUNT": "DDF927EE5DF25454",
    "bdindexid": "0dhdcn95g5smrgufo0hhfvmvo4",
    "SIGNIN_UC": "70a2711cf1d3d9b1a82d2f87d633bd8a05024333944bDF%2BzQcbPwkMP3otYlzv7RkSoCfMTEgN3IIB5JwXwy30FrBvReo2NHFChN%2BZ2dS7gG5SedkPY5XB0NVTxkpvu7smS%2Bm2hXjvVryxZdpID7AFFaVfZIg9g1SAe2LSUa9hcHlV%2FE2Yj%2BogT2A4qZHKE5M%2BFYJRqb2r6jjI9QaQzMhWXMNRT57l%2FKjoANb2fPc2zdygxyjtjTvpQ60%2F6sjg1fwsAJtgGfBc9qhC%2F%2FCJEL07q5j%2FRgeqGX25LpAAQ16J6V%2Bdl7LlAakuZzmarg9lnE%2FwQhBHBqlfqRRt16Us0cb8cb3ImpIxvMkxuI3dDA54h9woe6zkohVFM%2BsLLYe94w%3D%3D52077378665440824289473499408364",
    "__cas__rn__": "502433394",
    "__cas__st__212": "b63d0ef9121c732ea0a1d411324c50253a3eee2dc3e9abe739e1bc8d37ca96c8044983d7a2721f05013a2b38",
    "__cas__id__212": "69563296",
    "CPTK_212": "2108014540",
    "CPID_212": "69563296",
    "Hm_lpvt_d101ea4d2a5c67dab98251f0b5de24dc": "1752423010",
    "BDUSS_BFESS": "3ZlcTY5VmdtR055LS0yWUZIekVwaXpQdlhhZTVWNkQ1RjJZd1Z2RjZlMnZKb0pvSVFBQUFBJCQAAAAAAAAAAAEAAABKXe14tuS25MCyxL625AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK-ZWmivmVpoa",
    "ab_sr": "1.0.1_NjgzZGQxYTc2N2RhMDc0OWRjYjczMzVmMTM1ODI2MGEwZmFhODJiYTIwMDcxYjg1ODU1NTBkZGM4NTExOTU1MWEyMzM5ZGNmYTBlYzlhMGI0ZjUyNmVhMDc4MDgxYzg1MGY0MjgwZWEwZGYxMzNhMmY2MWM2NzBhYWVhNjU0YjMwMTY4OTg2MjQ0Y2JjOWZmMjhjYjdhMjgxODlhNmM1Yw==",
    "RT": "\"z=1&dm=baidu.com&si=454d90be-3dae-4ce7-84a2-ab2e9d648c5d&ss=md1qkfpj&sl=u&tt=zld&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ld=6paiy\""
}
url = "https://index.baidu.com/Interface/ptbk"
params = {
    "uniqid": "f841369741d1e68273df89dedac923b6"
}
response = requests.get(url, headers=headers, cookies=cookies, params=params)

print(response.text)
print(response)