"""
搜索指数爬虫（日度、周度数据和整体统计数据）
"""
import pandas as pd
import requests
import json
import time
from datetime import datetime
import threading
import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.logger import log
from utils.rate_limiter import rate_limiter
from utils.retry_decorator import retry
from utils.cipher_text import cipher_text_generator
from cookie_manager.cookie_rotator import cookie_rotator
from config.settings import BAIDU_INDEX_API
from fake_useragent import UserAgent
ua = UserAgent()
useragent=ua.random#随机生成seragent


# 原始的城市字典（城市代码到城市名称的映射）
city = {
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

            # 构建请求URL

cookies = {
    'BDUSS': '1QWW1LZnJFWDVPN350SDV6dWJTZHRNWnhWeEFjSVpPckduLTRMakQyRGhoa1ZvSVFBQUFBJCQAAAAAAAAAAAEAAABGVUcnzOy6o9PAs7oAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOH5HWjh-R1oM2',
    'BAIDUID': 'E8C2F89B2338E88F38F4D0A154FC1B64:SL=0:NR=50:FG=1',
    'HMACCOUNT': 'B14ADDE7C745CD61',
}


# 目标：爬取百度指数所有数据包括：
# 1. 搜索指数（包括日度数据、年度数据以及周度数据，以及时间区间内的整体日均值、移动日均值、整体同比、整体环比、移动同比、移动环比）可选的条件参数：时间：7天、30天、90天、半年，以及自定义时间；城市：全国，375个地级市；PC+移动端、PC端、移动端选择；
# 请求的headers和参数如下：
keyword = '电脑'
area = 0
start_date = '2024-01-01'
end_date = '2024-12-31'
encoded_keyword = keyword.replace(' ', '%20')
url = f'{BAIDU_INDEX_API['search_url']}?area={area}&word=[[{{"name":"{encoded_keyword}","wordType":1}}]]&startDate={start_date}&endDate={end_date}'
# url = f'{BAIDU_INDEX_API['search_url']}?area={area}&word=[[{{"name":"{encoded_keyword}","wordType":1}}]]&days={days}'
# days可以=7、30、90、180，或者不加days参数，就代表全部。area默认为0，代表全国
# word可以为：[[{"name":"电脑","wordType":1}],[{"name":"衣服","wordType":1}]]这样多个参数，表示对比
# 生成Cipher-Text参数
cipher_url = f'{BAIDU_INDEX_API['referer']}#/trend/{encoded_keyword}?words={encoded_keyword}'
cipher_text = cipher_text_generator.generate(cipher_url)
headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Cache-Control': 'no-cache',
    'Cipher-Text': cipher_text,
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Referer': BAIDU_INDEX_API['referer'],
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': useragent,
    'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    # 'Cookie': 'BAIDU_WISE_UID=wapp_1744869667916_527; BAIDUID=FF85DF65CC7463F3726D5301B69C0672:FG=1; BAIDUID_BFESS=FF85DF65CC7463F3726D5301B69C0672:FG=1; PSTM=1744882843; BIDUPSID=950D047CF79B4A0F8F86462CD08D849F; ZFY=:AYs:BOm:Ajfa1cQtiOrSJADVlDld3:BYmMcahDksItTkOQ:C; H_PS_PSSID=61027_62325_62485_62967_63042_63044_63140_63074_63189_63194_63210_63226_63242_63244_63249_63253; __bid_n=18c42450fcc02886ca93f5; BDUSS=3ZlcTY5VmdtR055LS0yWUZIekVwaXpQdlhhZTVWNkQ1RjJZd1Z2RjZlMnZKb0pvSVFBQUFBJCQAAAAAAAAAAAEAAABKXe14tuS25MCyxL625AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK-ZWmivmVpoa; Hm_lvt_d101ea4d2a5c67dab98251f0b5de24dc=1750687271,1750768658; HMACCOUNT=DDF927EE5DF25454; SIGNIN_UC=70a2711cf1d3d9b1a82d2f87d633bd8a05007811055iHW74BOJZpR8fIXeOGeBx5M6y7phE8fVUA6A5%2FT9V%2FlsHxmc8X4j0VNC%2F9LwP2zmQdfNMKxnxGOsso9i6z5EBqAppSnxsfJ24BKZ2HbQq2iyXFknWsLKsmgGjJw1B4gnKBPQaKQ17uqsRk7kRjIMxMQ9I09xx2H5mLprCONYZIbGfHaYp1BTvGG6rrGQtybXmNaMwxxsWVpk5FXOZ9eQ4K3Wkdor%2FZuxF6vZoZZboMBLW7wT1x8%2FnAf2M49uCYlG7sR%2B%2F2vpsj8pGF1p7tZvY9RSVz9Zuo7VoVT643%2FkQeIjx7VwkUgLo5BwXQ4wGzR60WWFDjO93A1KqcAW0Cufkg%3D%3D19042442273391681046897992923981; __cas__st__212=bbc20157a0eb310bf75a06fe47852349e3fdc208669fbd29ee3ef0f2081a8a25ae8d802c8eff57ed1747ef5a; __cas__id__212=69563296; __cas__rn__=500781105; CPTK_212=1747583717; CPID_212=69563296; bdindexid=l77euiikmgtpd8veg6574pg9b0; RT="z=1&dm=baidu.com&si=454d90be-3dae-4ce7-84a2-ab2e9d648c5d&ss=mcevsr5d&sl=1&tt=1fw&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf"; Hm_lpvt_d101ea4d2a5c67dab98251f0b5de24dc=1751032944; ab_sr=1.0.1_NzBjMmQ3NDQxYmZjMzM1YjliYTRmNWI0ZDhkNDc2MmYxMGRjYjkxOTJmNWVhZjg3MGJjODg3MTY1MWIyMGJjZWNhOTczOTAwZGE1MWM0NzVkNjU4YTQwMjJiMGRiZmQ0N2MyNTQwZDZhNDgxZjk1YzY4ZDBkMTU0MGNmODA2ZTNmMTQyODJhMDkxNDhiNDEwNzFhNWJjOGVlNGJkYjc0OQ==; BDUSS_BFESS=3ZlcTY5VmdtR055LS0yWUZIekVwaXpQdlhhZTVWNkQ1RjJZd1Z2RjZlMnZKb0pvSVFBQUFBJCQAAAAAAAAAAAEAAABKXe14tuS25MCyxL625AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAK-ZWmivmVpoa',
}

response = requests.get(
    url,
    cookies=cookies,
    headers=headers,
)
# 解密日度数据/周度数据（如果时间跨度为一年以上的话）
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
    url = f'https://index.baidu.com/api/SearchApi/index?area={city_number}&word=[[{{"name":"{word}","wordType":1}}]]&startDate={startDate}&endDate={endDate}'

    # 发送请求获取数据
    response = requests.get(url, cookies=cookies, headers=headers)
    time.sleep(3)
    return response.json()

# 获取解密密钥
def get_key(uniqid):
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

 