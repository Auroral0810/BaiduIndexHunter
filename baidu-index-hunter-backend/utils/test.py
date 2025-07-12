import requests


headers = {
    "Accept": "application/json, text/plain, */*",
    "Sec-Fetch-Site": "same-origin",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Sec-Fetch-Mode": "cors",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1.1 Safari/605.1.15",
    "Referer": "https://index.baidu.com/v2/main/index.html",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Cipher-Text": "1752293151482_1752327320019_f4Jtu9TdoRRhJ6UMWWA34n6OtnpZbDygnL8RD+LcIMtfe0Q0dAKRFW38bIH2d5okt1ag94NxtcHbLl1FLvzinY+QLkmlX9q3ROUJZz1OUB0wC84Ub5ZTJnQNJWH6UcBkKIgbR/legunU0KkK7f6D6/OG/J4BeefXmpuJ1004SNqgQNlQ2ax+9WTlJJO7ooMT0/YrXyxU+5NbMAIrC7N2q/bXFIPyiMmkmA5cesCzz99a+9X30DaiEhy/ckeQMrMuroUWlwb3eiyx0FGkmI9SAkEVpjyiPTmU8kd9OQE+JxTQaZRbfoqJ2tBapnBANz5AoJE188hf8UfVYCSHtll4CRLuzk6Rq87gP3RfPcYXiAcwZYzZOKuYTRN7EPvwO2Ey3PDTSjBXjT/Obi2t9Oo7ig==",
    "Priority": "u=3, i"
}
cookies = {
    "RT": "\"z=1&dm=baidu.com&si=443db7dc-2198-4d2c-a0aa-a4f07c5d4622&ss=md0a7sfq&sl=4&tt=7ty&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf\"",
    "ab_sr": "1.0.1_OTk4MjQ2Mzg1MTQyZGUyZmQ1NTNhMmJhMDVhODVhZmQzZGIzMTU3ZDk4ZWFlNzNjM2ViOGU5NGRlYWU2YjBiMDBmODgwMmQ1MzQ3NGFjNGYyZGNkMzZjZGIzZWY5YTAxNjA3YTZjNzI1YWEyOWJmZjhiNTc5ZDAxNGU0ZGIxNzQyMzc2MjJiN2QzZWZkMTI5NjRiNGY1NGQ1OTk2ZjQxZg==",
    "Hm_lpvt_d101ea4d2a5c67dab98251f0b5de24dc": "1752327319",
    "Hm_lvt_d101ea4d2a5c67dab98251f0b5de24dc": "1750763806,1751030539,1751277513,1752326945",
    "bdindexid": "5cuoofs9fkoo0q7q00sm2t9m01",
    "CPID_212": "69554690",
    "CPTK_212": "1992776441",
    "__cas__id__212": "69554690",
    "__cas__rn__": "502339394",
    "__cas__st__212": "652e44ef036a6243543c908a2edcdb8b9842f2219ece48085428583d68fe518bc68f1bbf2a5e01447bec40ee",
    "SIGNIN_UC": "70a2711cf1d3d9b1a82d2f87d633bd8a05023393944IxyvKHy4t5kWE8URKzfx5SIqVBJrskXE21l5qQZGIWrMs4YcKcCpRVIInQPssPQGKtHw50bS8qHE1Ha7XV616AVEvK%2BacjK%2BfZkbNMMI%2FhOlAz18U6Qik2FlH4owdmRwMDmbmZ0VTlPbOWcrIacmXbDut9vZ5%2FzzHLu6e0PbsTUlRPydrzw3rr1MmqX7nmb2ANKRCdmFCxoBCMQyP08tN5q4sIf6PSaDbdHVlNq4TcllStnBLbOeSw2cvt9gIUg0nRifwWpzPT0e1MGfvBj8cQ%3D%3D26334470087675246505739073688438",
    "HMACCOUNT": "496483824474D6A5",
    "BDORZ": "FFFB88E999055A3F8A630C64834BD6D0",
    "ZFY": "eZolgqFOY0Y0f1Qg:AhsGZTGexoRJ:Ah9e:AUlH93hdW8c:C",
    "BA_HECTOR": "ak00a58081al212k8h81250ka4ag021k74oor25",
    "BDRCVFR[d9MwMhSWl4T]": "mk3SLVN4HKm",
    "H_PS_PSSID": "60279_61684_62325_63144_63324_63724_63728_63778_63819_63881_63887_63921_63950_63948_63957_63989_63275_64012_64027_64031",
    "PSINO": "3",
    "delPer": "0",
    "BDUSS": "5wSkM5U2F2U0kwQWJTcVhwdWtJZHR-ZTNxU2ppVXhicFFTcllqUXI2RmlUNEpvSVFBQUFBJCQAAAAAAQAAAAEAAADqGBSHQXVyb3JhbDY4NjgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGLCWmhiwlpoR0",
    "H_WISE_SIDS": "60279_61684_62325_62967_63144_63194_63210_63241_63268_63324_63352_63386_63394_63390_63440",
    "BIDUPSID": "2FEBFD961790CF3B5CB7C06D0DCA03F8",
    "PSTM": "1745642057",
    "BAIDUID": "5E9B2757D9152FB85FDD6D4AEB4026ED:FG=1",
    "MAWEBCUID": "web_oHAxQIUvPYLZZQqNfndpkAqAJlTBpabDPBBNaCvdMXrswtkRXG",
    "MCITY": "-%3A"
}
url = "https://index.baidu.com/api/SearchApi/index"
params = {
    "area": "0",
    "word": "[[{'name':'电脑','wordType':1}]]",
    "days": "30"
}
response = requests.get(url, headers=headers, cookies=cookies, params=params)

print(response.text)
print(response)