import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import time
from fake_useragent import UserAgent
import execjs


ua = UserAgent()
useragent=ua.chrome#随机生成谷歌浏览器的useragent，想要各种浏览器的改chrome为randome


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


# 请求接口获取数据
def get_data(city_number, word, startDate, endDate):
    # 构建请求URL
    url = f'https://index.baidu.com/api/SearchApi/index?area={city_number}&word=[[{{"name":"{word}","wordType":1}}]]&startDate={startDate}&endDate={endDate}'
    word1 = f'{word},手机'
    url_cipyter = f'https://index.baidu.com/v2/main/index.html#/trend/{word}?words={word1}'
    
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
        "Hm_lpvt_d101ea4d2a5c67dab98251f0b5de24dc": "1768718716",
        "BDUSS_BFESS": "U1heFFnbmJQb01jZnJoTjQ1TEl-TGh-eVYzbWswUm52ajduRktCeElHakVmb3hwSVFBQUFBJCQAAAAAAQAAAAEAAACSeU9mTHVja19mZjA4MTAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMTxZGnE8WRpe",
        "ab_sr": "1.0.1_NzU4MGRkMzU5MzY2NGE3NjU5OTIwYThmZDk3OWUzZjIwNzY5Njk5YTlmNTUxZDE3ZWM4OThkYWEwNGUyM2UxMzg4OTMzZTg2Y2NkOTNmMDdlMjQ1YmYzM2I0NzY3YmJjNTJkNzYyYWQ3OTQxODMxNmE5ZmJmM2Y1ZjMzOWQ0MWQ1YWVhMWJjMjE4YTA5NDM1YjNiNDhhNDI5OGMxNjA4Mg==",
        "RT": "\"z=1&dm=baidu.com&si=9f0a8178-99ee-438a-8de7-d74859b355dc&ss=mkhu19uc&sl=ok&tt=3e6f&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ld=z7kx&nu=2ua2g7gp&cl=10m0j&ul=10m0q&hd=1jf5o3\""
    }
    # 构建请求URL
    url = f'https://index.baidu.com/api/SearchApi/index?area={city_number}&word=[[{{"name":"{word}","wordType":1}}]]&startDate={startDate}&endDate={endDate}'
    word1 = f'{word},手机'
    url_cipyter = f'https://index.baidu.com/v2/main/index.html#/trend/{word}?words={word1}'

    with open('Cipher-Text.js', 'r') as f:
        js = f.read()
        ctx = execjs.compile(js)
    cipyer_text=ctx.call('ascToken',url_cipyter)
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

    # 发送请求获取数据
    response = requests.get(url, cookies=cookies,headers=headers)
    time.sleep(1)
    return response.json()

# 分析数据
def analyze_data(data, city_number, city_name, word, year):
    try:
        # 获取统计数据
        generalRatio_all_avg = data['data']['generalRatio'][0]['all']['avg'] # 整体日均值
        generalRatio_wise_avg = data['data']['generalRatio'][0]['wise']['avg'] # 移动日均值
        generalRatio_pc_avg = data['data']['generalRatio'][0]['pc']['avg'] # PC日均值

        # 计算年份的天数
        def get_days_in_year(year):
            if year == 2025:  # 2025年只统计到6月23日
                return (datetime(2025, 6, 23) - datetime(2025, 1, 1)).days + 1
            elif (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):  # 闰年
                return 366
            else:  # 平年
                return 365
        
        # 获取当前年份的天数
        days_in_year = get_days_in_year(year)
        
        # 创建数据框
        df = pd.DataFrame({
            '搜索关键词': [word],
            '城市': [city_name],
            '年份': [year],
            '整体日均值': [generalRatio_all_avg],
            '移动日均值': [generalRatio_wise_avg],
            'PC日均值': [generalRatio_pc_avg],
            '整体年总值': [generalRatio_all_avg * days_in_year],
            '移动年总值': [generalRatio_wise_avg * days_in_year],
            'PC年总值': [generalRatio_pc_avg * days_in_year]
        })
        
        return df
    except (TypeError, KeyError) as e:
        print(f"数据解析错误: {e}")
        print(f"原始数据: {data}")
        # 返回空数据框
        return pd.DataFrame()


if __name__ == "__main__":
    # 读取关键词列表
    try:
        word_list = pd.read_excel('数字设备和服务关键词.xlsx')
        keywords = word_list['关键词'].tolist()
        print(f"成功读取到 {len(keywords)} 个关键词")
    except Exception as e:
        print(f"读取关键词文件失败: {str(e)}")
        print("使用默认关键词'数字政务APP'继续")
        keywords = ["数字政务APP"]
    
    years = range(2016, 2026)  # 2016年到2025年
    
    # 用于合并所有数据的DataFrame
    all_data = []
    
    # 循环遍历所有关键词
    for word in keywords:
        print(f"\n开始爬取关键词: {word}")
        
        # 循环遍历所有年份
        for year in years:
            startDate = f"{year}-01-01"
            endDate = f"{year}-12-31"
            
            # 如果是2025年，结束日期为2025-06-23
            if year == 2025:
                endDate = "2025-06-23"
                
            # 循环遍历所有城市
            for city_number, city_name in city.items():
                print(f"正在获取 {word} 在 {city_name}({city_number}) 的 {year}年 数据...")
                try:
                    data = get_data(city_number, word, startDate, endDate)
                    df = analyze_data(data, city_number, city_name, word, year)
                    
                    if not df.empty:
                        # 将当前数据添加到总数据中
                        all_data.append(df)
                    
                    print(f"{word} 在 {city_name} {year}年 数据获取成功")
                except Exception as e:
                    print(f"{word} 在 {city_name} {year}年 数据获取失败: {str(e)}") 
                break
            break
        break
    
    # 合并所有数据
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # 保存到Excel文件
        excel_path = "百度指数_全部关键词.xlsx"
        combined_df.to_excel(excel_path, index=False)
        
        print(f"所有数据已保存到 {excel_path}")
    else:
        print("没有获取到任何有效数据")
