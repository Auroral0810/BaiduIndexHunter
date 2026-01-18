import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import time
from fake_useragent import UserAgent
import execjs
ua = UserAgent()
useragent=ua.chrome#随机生成谷歌浏览器的useragent，想要各种浏览器的改chrome为randome

cookies = {
  "BAIDUID": "BB069E74A97B4457314AF9E557A775B5:FG=1",
  "BDUSS": "nRDcE04eXo3alhWUTNKMEl3OFA3UGpRWml-YXJ0T0F5NkVtTnFUZFluTTVTcHRvSVFBQUFBJCQAAAAAAQAAAAEAAACSeU9mTHVja19mZjA4MTAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADm9c2g5vXNoe",
  "BIDUPSID": "BB069E74A97B445759DF452FC47CF33C",
  "CPID_212": "69553869",
  "CPTK_212": "827188108",
  "HMACCOUNT": "27C1B7F9FD18913C",
  "H_PS_PSSID": "61671_62325_63145_63402_63559_63582_63579_63636_63645_63647_63657_63685_63693_63725_63726_63721_63274_63754_63776",
  "Hm_lpvt_d101ea4d2a5c67dab98251f0b5de24dc": "1752416415",
  "Hm_lvt_d101ea4d2a5c67dab98251f0b5de24dc": "1751182461,1751274263,1752349920,1752415526",
  "PSTM": "1750817887",
  "RT": "\"z=1^&dm=baidu.com^&si=02fed619-23f0-4cfe-a747-6fecbb73c9e7^&ss=md1qyhdf^&sl=6^&tt=ezn^&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf\"",
  "SIGNIN_UC": "70a2711cf1d3d9b1a82d2f87d633bd8a05024279944MdIKS8G%2Fj05KnpQHiY9U8dVbHCfG9xBDFdmvw4W6y9SN5hdI4V0NiymmZRFhLIU6HoA3SOw73WUEYdDWSmByUJd21IDqQTqpDMRMHqRkA4C13Myf%2BX4UfnQF2loS4DI37VFzKqb2MR21eyhfQrn%2FHZhgKqsiXcSwobvvoq7zONiQW93xiRuzMDmkP09WhGcgyA8qqx0On6t1TDI%2Be66Yjx4QQ3Cgt%2FeXJ7%2FjiraqYNLrRkSazYJ495j3FBG5c6ORuUBWb%2FwQPaFYJ%2Fg2MG4vlg%3D%3D27520805628177446514338450553146",
  "ZFY": "Ys35EjG1tLOOy87JpBudB4kv2T3jlkknwwJRbbpCoWs:C",
  "__cas__id__212": "69553869",
  "__cas__rn__": "502427994",
  "__cas__st__212": "b7d1a414403f3b12c97c2e25a41085884848b8c50e32c181403c91633fc925e6dd63f09d2639519fbe29d4b5",
  "ab_sr": "1.0.1_MTczNWJlMDdiODA0OWI1MjQxYTM0Zjg1NGU2Njk4ZjJjMDAwYjRkMjg5NDQ5ZDEwZmNkMjU0YjljMTgwMWE1YjQ4M2YzMTU1N2UyMDA5NTI1NDQ2MGM4MWRlZDNkM2YyNmE0YjBmMmFiODhkYzdjZTZkNDc4MDNkODgyZmJlY2MxZDViZmMwNGE4MDc0MzkyNjA3MzdjMGM3OTY4NDU0Ng==",
  "bdindexid": "ag401f10k80h5dptlc2mjfuln6",
  "ppfuid": "FOCoIC3q5fKa8fgJnwzbE0LGziLN3VHbX8wfShDP6RCsfXQp/69CStRUAcn/QmhIlFDxPrAc/s5tJmCocrihd0enHWGiHNa8jc3p2YbsY9AALyh5vL2Qlx5tbhvZJfQoJpuXZiPIDDB1PsImjYrujaLB0a5/KhEJDV/FkT58huuCglJtQa4Nv6My3pbEqyAN2BNB27wAj+4roh5lwb9vzPJqqOF3TCRm2tJa1EDuY8YDN3WmJY/NWBcNvpqdRBdKrEEfvwQKWpWE08OG0Oa852CXWQYpvBie32q9dmRfwfjHu7PS+78rSATuF9ZmxajHuK36gVAlel31+rZpX2v1w0G3gqifdSzT35NQlL/KGVZl29TNM8Tn9jGWq9feGmPlmfSlGcsA4Zw7tT4tSNMvZJd3rjLXF5IlRLmU2zoPN2oWXej9z+plTsDB5x+aCBWPx2RTt0mgeBku85QaxtnC5vJU0ZdfSWHGHKr8tz/+dJsaVg8FFAuKbyjhfXvqcDau5eh8yhGcgjFA3flugImpLGIrvuAAM+9jpzEH4AMjVG1tyMsy+XPlAYbfO1lIoDmPWpXCLkfp9YMJ/g5n97pwE2Brb9MypgKINzcvcBWIkP4HSkq0fQ9uR0sKy0MiHuUCk5CkpWOp1Xr/DIWk9wFD8KCJLToVpiOq1G0BHRvSH1+YLQpEgFjmQoey69Fz+kM7Y5cg925MGCeBU4jWp2g2g4jLwO5m3xbqox7eAsiXWhrTecoxj1GLijlUYBSGerO+YdBrxFfXZ8kxisvFxYwkIrjbCSee7nPW0+PyJuXQBgjcbXIXMwzaWncDMKa6N8mYTcDDS/X2OsuXb3TbCGrHK4HeDpCtd6RMvOgbCfDNICl4LYr1IDPAY5dZv6ZINErg8p7Vi3a5jMXGWL4Mkr0ksENkLZvBJChyDMkf14Hx56V+b2nRqUTK6NqmhPLvsfMNYCRyESom9rukNSbUImRNUXXv70cfMSn4OrmEd+59Ab34CROfim3rsAsgLyURlANn6bdFQpSH1dJtj0Ru27x9NDjgymOnBYuzYFgCuiXNRuEnPBCCiO27dL+MWrnVYSkeCARd+2gYcoj1jwDnmFwagA=="
}



city =  {
        1: "济南",
        2: "贵阳",
        3: "黔南",
        4: "六盘水",
        5: "南昌",
        6: "九江",
        7: "鹰潭",
        8: "抚州",
        9: "上饶",
        10: "赣州",
        11: "重庆",
        13: "包头",
        14: "鄂尔多斯",
        15: "巴彦淖尔",
        16: "乌海",
        17: "阿拉善盟",
        19: "锡林郭勒盟",
        20: "呼和浩特",
        21: "赤峰",
        22: "通辽",
        25: "呼伦贝尔",
        28: "武汉",
        29: "大连",
        30: "黄石",
        31: "荆州",
        32: "襄阳",
        33: "黄冈",
        34: "荆门",
        35: "宜昌",
        36: "十堰",
        37: "随州",
        38: "恩施",
        39: "鄂州",
        40: "咸宁",
        41: "孝感",
        42: "仙桃",
        43: "长沙",
        44: "岳阳",
        45: "衡阳",
        46: "株洲",
        47: "湘潭",
        48: "益阳",
        49: "郴州",
        50: "福州",
        51: "莆田",
        52: "三明",
        53: "龙岩",
        54: "厦门",
        55: "泉州",
        56: "漳州",
        57: "上海",
        59: "遵义",
        61: "黔东南",
        65: "湘西",
        66: "娄底",
        67: "怀化",
        68: "常德",
        73: "天门",
        74: "潜江",
        76: "滨州",
        77: "青岛",
        78: "烟台",
        79: "临沂",
        80: "潍坊",
        81: "淄博",
        82: "东营",
        83: "聊城",
        84: "菏泽",
        85: "枣庄",
        86: "德州",
        87: "宁德",
        88: "威海",
        89: "柳州",
        90: "南宁",
        91: "桂林",
        92: "贺州",
        93: "贵港",
        94: "深圳",
        95: "广州",
        96: "宜宾",
        97: "成都",
        98: "绵阳",
        99: "广元",
        100: "遂宁",
        101: "巴中",
        102: "内江",
        103: "泸州",
        104: "南充",
        106: "德阳",
        107: "乐山",
        108: "广安",
        109: "资阳",
        111: "自贡",
        112: "攀枝花",
        113: "达州",
        114: "雅安",
        115: "吉安",
        117: "昆明",
        118: "玉林",
        119: "河池",
        123: "玉溪",
        124: "楚雄",
        125: "南京",
        126: "苏州",
        127: "无锡",
        128: "北海",
        129: "钦州",
        130: "防城港",
        131: "百色",
        132: "梧州",
        133: "东莞",
        134: "丽水",
        135: "金华",
        136: "萍乡",
        137: "景德镇",
        138: "杭州",
        139: "西宁",
        140: "银川",
        141: "石家庄",
        143: "衡水",
        144: "张家口",
        145: "承德",
        146: "秦皇岛",
        147: "廊坊",
        148: "沧州",
        149: "温州",
        150: "沈阳",
        151: "盘锦",
        152: "哈尔滨",
        153: "大庆",
        154: "长春",
        155: "四平",
        156: "连云港",
        157: "淮安",
        158: "扬州",
        159: "泰州",
        160: "盐城",
        161: "徐州",
        162: "常州",
        163: "南通",
        164: "天津",
        165: "西安",
        166: "兰州",
        168: "郑州",
        169: "镇江",
        172: "宿迁",
        173: "铜陵",
        174: "黄山",
        175: "池州",
        176: "宣城",
        177: "巢湖",
        178: "淮南",
        179: "宿州",
        181: "六安",
        182: "滁州",
        183: "淮北",
        184: "阜阳",
        185: "马鞍山",
        186: "安庆",
        187: "蚌埠",
        188: "芜湖",
        189: "合肥",
        191: "辽源",
        194: "松原",
        195: "云浮",
        196: "佛山",
        197: "湛江",
        198: "江门",
        199: "惠州",
        200: "珠海",
        201: "韶关",
        202: "阳江",
        203: "茂名",
        204: "潮州",
        205: "揭阳",
        207: "中山",
        208: "清远",
        209: "肇庆",
        210: "河源",
        211: "梅州",
        212: "汕头",
        213: "汕尾",
        215: "鞍山",
        216: "朝阳",
        217: "锦州",
        218: "铁岭",
        219: "丹东",
        220: "本溪",
        221: "营口",
        222: "抚顺",
        223: "阜新",
        224: "辽阳",
        225: "葫芦岛",
        226: "张家界",
        227: "大同",
        228: "长治",
        229: "忻州",
        230: "晋中",
        231: "太原",
        232: "临汾",
        233: "运城",
        234: "晋城",
        235: "朔州",
        236: "阳泉",
        237: "吕梁",
        239: "海口",
        241: "万宁",
        242: "琼海",
        243: "三亚",
        244: "儋州",
        246: "新余",
        253: "南平",
        256: "宜春",
        259: "保定",
        261: "唐山",
        262: "南阳",
        263: "新乡",
        264: "开封",
        265: "焦作",
        266: "平顶山",
        268: "许昌",
        269: "永州",
        270: "吉林",
        271: "铜川",
        272: "安康",
        273: "宝鸡",
        274: "商洛",
        275: "渭南",
        276: "汉中",
        277: "咸阳",
        278: "榆林",
        280: "石河子",
        281: "庆阳",
        282: "定西",
        283: "武威",
        284: "酒泉",
        285: "张掖",
        286: "嘉峪关",
        287: "台州",
        288: "衢州",
        289: "宁波",
        291: "眉山",
        292: "邯郸",
        293: "邢台",
        295: "伊春",
        297: "大兴安岭",
        300: "黑河",
        301: "鹤岗",
        302: "七台河",
        303: "绍兴",
        304: "嘉兴",
        305: "湖州",
        306: "舟山",
        307: "平凉",
        308: "天水",
        309: "白银",
        310: "吐鲁番",
        311: "昌吉",
        312: "哈密",
        315: "阿克苏",
        317: "克拉玛依",
        318: "博尔塔拉",
        319: "齐齐哈尔",
        320: "佳木斯",
        322: "牡丹江",
        323: "鸡西",
        324: "绥化",
        331: "乌兰察布",
        333: "兴安盟",
        334: "大理",
        335: "昭通",
        337: "红河",
        339: "曲靖",
        342: "丽江",
        343: "金昌",
        344: "陇南",
        346: "临夏",
        350: "临沧",
        352: "济宁",
        353: "泰安",
        356: "莱芜",
        359: "双鸭山",
        366: "日照",
        370: "安阳",
        371: "驻马店",
        373: "信阳",
        374: "鹤壁",
        375: "周口",
        376: "商丘",
        378: "洛阳",
        379: "漯河",
        380: "濮阳",
        381: "三门峡",
        383: "阿勒泰",
        384: "喀什",
        386: "和田",
        391: "亳州",
        395: "吴忠",
        396: "固原",
        401: "延安",
        405: "邵阳",
        407: "通化",
        408: "白山",
        410: "白城",
        417: "甘孜",
        422: "铜仁",
        424: "安顺",
        426: "毕节",
        437: "文山",
        438: "保山",
        456: "东方",
        457: "阿坝",
        466: "拉萨",
        467: "乌鲁木齐",
        472: "石嘴山",
        479: "凉山",
        480: "中卫",
        499: "巴音郭楞",
        506: "来宾",
        514: "北京",
        516: "日喀则",
        520: "伊犁",
        525: "延边",
        563: "塔城",
        582: "五指山",
        588: "黔西南",
        608: "海西",
        652: "海东",
        653: "克孜勒苏柯尔克孜",
        654: "天门仙桃",
        655: "那曲",
        656: "林芝",
        657: "None",
        658: "防城",
        659: "玉树",
        660: "伊犁哈萨克",
        661: "五家渠",
        662: "思茅",
        663: "香港",
        664: "澳门",
        665: "崇左",
        666: "普洱",
        667: "济源",
        668: "西双版纳",
        669: "德宏",
        670: "文昌",
        671: "怒江",
        672: "迪庆",
        673: "甘南",
        674: "陵水黎族自治县",
        675: "澄迈县",
        676: "海南",
        677: "山南",
        678: "昌都",
        679: "乐东黎族自治县",
        680: "临高县",
        681: "定安县",
        682: "海北",
        683: "昌江黎族自治县",
        684: "屯昌县",
        685: "黄南",
        686: "保亭黎族苗族自治县",
        687: "神农架",
        688: "果洛",
        689: "白沙黎族自治县",
        690: "琼中黎族苗族自治县",
        691: "阿里",
        692: "阿拉尔",
        693: "图木舒克"
    }
# print(len(city))

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

# 解密趋势数据
def decrypt_trend(key, data):
    return decrypt(key, data)

# 请求接口获取数据
def get_data(city_number, word, startDate, endDate):
    # 构建请求URL
    word1 = f'{word},手机'
    url_cipyter = f'https://index.baidu.com/v2/main/index.html#/trend/{word}?words={word1}'

    with open('Cipher-Text.js', 'r') as f:
        js = f.read()
        ctx = execjs.compile(js)
    cipyer_text = ctx.call('ascToken', url_cipyter)
    print(cipyer_text)
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
        # 'Cookie': 'BAIDU_WISE_UID=wapp_1744869667916_527; BAIDUID=FF85DF65CC7463F3726D5301B69C0672:FG=1; BAIDUID_BFESS=FF85DF65CC7463F3726D5301B69C0672:FG=1; PSTM=1744882843; BIDUPSID=950D047CF79B4A0F8F86462CD08D849F; ZFY=:AYs:BOm:Ajfa1cQtiOrSJADVlDld3:BYmMcahDksItTkOQ:C; __bid_n=18c42450fcc02886ca93f5; BDUSS=3ZlcTY5VmdtR055LS0yWUZIekVwaXpQdlhhZTVWNkQ1RjJZd1Z2RjZlMnZKb0pvSVFBQUFBJCQAAAAAAAAAAAEAAABKXe14tuS25MCyxL625AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK-ZWmivmVpoa; H_PS_PSSID=62325_63140_63324_63401_63584_63638_63643_63647_63659_63724_63712_63749_63756; Hm_lvt_d101ea4d2a5c67dab98251f0b5de24dc=1751181661,1751210338,1751213710,1751243261; HMACCOUNT=DDF927EE5DF25454; SIGNIN_UC=70a2711cf1d3d9b1a82d2f87d633bd8a0501255709984FEi9UEKliGHWSHXZ6oYd17WpvF4UpTpi0S%2FMkYmfiNAqK1M0jX%2FRqCmmXdrDEKGvA1CsZHHN0J6ilBmnFop%2F8%2B6kq5c6KzFnXz9L69g0uZoezgZ760lQ3%2FUb20RzzXNbk81Z8UtRs%2FPC06mHQdR82YpdoLC1zwfBABKuYj%2BJSlme6%2FJz8fJh4BK9HFN2Wz3RmPvMQj1MCnGMm79Lwvycr04s7oj8%2FcIHSQ4uxrGwiuKRkD%2BW0QDFVw%2FJv4smgVX%2BEyECGZwW%2BO0NxOEr65Tck9T8YE1aDXFoucNxhXryU4iEwfAomNvsLSlXKVdvtppWhAXzpyghmbU5%2BSA%2BJUIw%3D%3D34813889920872661871379264310074; __cas__rn__=501255709; __cas__st__212=8667dbced52a16d95b022f15621d78910c7bb72005387e9d4326869b031a70d6907b3470b90ff2b24eeeb20d; __cas__id__212=69563296; CPTK_212=1532251641; CPID_212=69563296; bdindexid=42r0a9do4patuegrcfi2pcmkl7; RT="z=1&dm=baidu.com&si=454d90be-3dae-4ce7-84a2-ab2e9d648c5d&ss=mcis9mum&sl=7&tt=5lm&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf"; Hm_lpvt_d101ea4d2a5c67dab98251f0b5de24dc=1751270136; ab_sr=1.0.1_MGEzOGQ3MjY3MjNkYmE3OTk0ZGEzNDJkNjhmZGU1MTZjZjc1OWMzNzBkODA0NDhkNWUxNGM2MTQzNDhhNzVhNjgzYjQ4ODQxOGY5MmY4NDYxYTY1YjJjYjNlNDZkYjkyMTJmMTNlN2U0NjIzZGJlMWI1MDI4OWEyMjExODIwNzAxYTQ2MzAxODhjMzBhOTA0ZTE3NGM4ZTNjY2UyNjVkMQ==; BDUSS_BFESS=3ZlcTY5VmdtR055LS0yWUZIekVwaXpQdlhhZTVWNkQ1RjJZd1Z2RjZlMnZKb0pvSVFBQUFBJCQAAAAAAAAAAAEAAABKXe14tuS25MCyxL625AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK-ZWmivmVpoa',
    }
    # 构建请求URL
    url = f'https://index.baidu.com/api/SearchApi/index?area={city_number}&word=[[{{"name":"{word}","wordType":1}}]]&startDate={startDate}&endDate={endDate}'

    # 发送请求获取数据
    response = requests.get(url, cookies=cookies, headers=headers)
    time.sleep(3)
    return response.json()

# 获取解密密钥
def get_key(uniqid):
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
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
    
    params = {
        'uniqid': uniqid,
    }

    response = requests.get('https://index.baidu.com/Interface/ptbk', params=params, cookies=cookies, headers=headers)

    key = response.json()['data'] # 解密密钥
    time.sleep(3)
    return key

# 分析数据
def analyze_data(data, city_number, city_name, word, startDate, endDate):
    try:
        userIndexes_all = data['data']['userIndexes'][0]['all']['data'] # 全部数据
        userIndexes_wise = data['data']['userIndexes'][0]['wise']['data'] # 移动数据
        userIndexes_pc = data['data']['userIndexes'][0]['pc']['data'] # PC数据
        uniqid = data['data']['uniqid'] # 唯一标识
        key = get_key(uniqid) # 解密密钥
        
        # 解密趋势数据
        decrypted_userIndexes_all = decrypt_trend(key, userIndexes_all)
        decrypted_userIndexes_wise = decrypt_trend(key, userIndexes_wise)
        decrypted_userIndexes_pc = decrypt_trend(key, userIndexes_pc)
        
        # 获取统计数据
        generalRatio_all_avg = data['data']['generalRatio'][0]['all']['avg'] # 整体日均值
        generalRatio_all_yoy = data['data']['generalRatio'][0]['all']['yoy'] # 整体同比
        generalRatio_all_qoq = data['data']['generalRatio'][0]['all']['qoq'] # 整体环比
        
        generalRatio_wise_avg = data['data']['generalRatio'][0]['wise']['avg'] # 移动日均值
        generalRatio_wise_yoy = data['data']['generalRatio'][0]['wise']['yoy'] # 移动同比
        generalRatio_wise_qoq = data['data']['generalRatio'][0]['wise']['qoq'] # 移动环比
        
        generalRatio_pc_avg = data['data']['generalRatio'][0]['pc']['avg'] # PC日均值
        generalRatio_pc_yoy = data['data']['generalRatio'][0]['pc']['yoy'] # PC同比
        generalRatio_pc_qoq = data['data']['generalRatio'][0]['pc']['qoq'] # PC环比
        
        # 将解密后的数据转换为列表
        all_data = decrypted_userIndexes_all.split(',')
        wise_data = decrypted_userIndexes_wise.split(',')
        pc_data = decrypted_userIndexes_pc.split(',')
        print(all_data)
        print(wise_data)
        print(pc_data)
        # 计算日期间隔
        start_date = datetime.strptime(startDate, '%Y-%m-%d')
        end_date = datetime.strptime(endDate, '%Y-%m-%d')
        total_days = (end_date - start_date).days + 1
        
        # 判断数据粒度
        data_length = len(all_data)
        
        # 确定数据间隔
        if data_length == total_days:
            # 每天一个数据点
            interval = 1
        elif abs(total_days - data_length * 7) <= 7:  # 允许有一定误差
            # 每周一个数据点
            interval = 7
        else:
            # 尝试确定其他间隔
            interval = total_days // data_length if data_length > 0 else 1
            
        print(f"{city_name} 数据粒度: 每{interval}天一个数据点")
        
        # 生成日期列表，根据数据粒度调整
        date_range = []
        for i in range(data_length):
            current_date = (start_date + timedelta(days=i*interval)).strftime('%Y-%m-%d')
            date_range.append(current_date)
            
    except TypeError as e:
        print(f"数据解析错误: {e}")
        print(f"原始数据: {data}")
        # 返回空数据框
        return pd.DataFrame(), pd.DataFrame()
    
    # 创建数据框
    df = pd.DataFrame({
        '城市': [city_name] * len(date_range),
        '日期': date_range,
        '数据间隔(天)': [interval] * len(date_range),
        '整体指数': all_data,
        '移动指数': wise_data,
        'PC指数': pc_data
    })
    
    # 创建统计数据框
    stats_df = pd.DataFrame({
        '城市': [city_name] * 3,
        '指标': ['日均值', '同比', '环比'],
        '整体': [generalRatio_all_avg, generalRatio_all_yoy, generalRatio_all_qoq],
        '移动': [generalRatio_wise_avg, generalRatio_wise_yoy, generalRatio_wise_qoq],
        'PC': [generalRatio_pc_avg, generalRatio_pc_yoy, generalRatio_pc_qoq]
    })
    
    return df, stats_df


if __name__ == "__main__":
    # word_list = pd.read_excel('word_list.xlsx')
    word = "人工智能"  # 可以根据需要修改
    startDate = "2024-01-01"
    endDate = "2024-12-31"

    
    # 创建以关键词和时间范围命名的文件夹
    folder_name = f"{word}_{startDate}至{endDate}_百度指数"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    # 用于合并所有城市数据的DataFrame
    all_trend_data = []
    all_stats_data = []
    
    # 循环遍历所有城市
    for city_number, city_name in city.items():
        print(f"正在获取 {city_name}({city_number}) 的数据...")
        try:
            data = get_data(city_number, word, startDate, endDate)
            df, stats_df = analyze_data(data, city_number, city_name, word, startDate, endDate)
            
            # 将当前城市数据添加到总数据中
            all_trend_data.append(df)
            all_stats_data.append(stats_df)
            
            print(f"{city_name} 数据获取成功")
            break
        except Exception as e:
            print(f"{city_name} 数据获取失败: {str(e)}")
    
    # 合并所有城市数据
    combined_trend_df = pd.concat(all_trend_data, ignore_index=True)
    combined_stats_df = pd.concat(all_stats_data, ignore_index=True)
    
    # 保存到Excel文件
    excel_path = os.path.join(folder_name, f"{word}_{startDate}至{endDate}_百度指数汇总.xlsx")
    with pd.ExcelWriter(excel_path) as writer:
        combined_trend_df.to_excel(writer, sheet_name='趋势数据', index=False)
        combined_stats_df.to_excel(writer, sheet_name='统计数据', index=False)
    
    print(f"所有城市数据已保存到 {excel_path}")
