import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import time
from fake_useragent import UserAgent
import execjs
import urllib.parse
import json
import logging

ua = UserAgent()
useragent = ua.chrome  # 随机生成谷歌浏览器的useragent

# 配置日志
def setup_logger(log_file='crawler_progress.log'):
    """设置日志记录器"""
    logger = logging.getLogger('crawler')
    logger.setLevel(logging.INFO)
    
    # 如果logger已经有handler，先清除
    if logger.handlers:
        logger.handlers.clear()
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 格式化器
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                                  datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 创建全局logger
logger = setup_logger()

# 任务进度文件
PROGRESS_FILE = 'crawler_progress.json'

def load_completed_tasks():
    """加载已完成的任务列表"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                completed_tasks = json.load(f)
                logger.info(f"加载已完成任务: {len(completed_tasks)} 个")
                return set(tuple(task) for task in completed_tasks)
        except Exception as e:
            logger.error(f"加载任务进度文件失败: {e}")
            return set()
    return set()

def save_completed_task(keyword, city_code, start_date, end_date):
    """保存已完成的任务"""
    completed_tasks = load_completed_tasks()
    task_key = (keyword, city_code, start_date, end_date)
    
    if task_key not in completed_tasks:
        completed_tasks.add(task_key)
        try:
            # 将set转换为list以便JSON序列化
            tasks_list = [list(task) for task in completed_tasks]
            with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump(tasks_list, f, ensure_ascii=False, indent=2)
            logger.info(f"任务已完成并保存: {keyword} - 城市代码{city_code} - {start_date}至{end_date}")
        except Exception as e:
            logger.error(f"保存任务进度失败: {e}")

def is_task_completed(keyword, city_code, start_date, end_date):
    """检查任务是否已完成"""
    completed_tasks = load_completed_tasks()
    task_key = (keyword, city_code, start_date, end_date)
    return task_key in completed_tasks

def print_completed_tasks():
    """打印已完成的任务列表"""
    completed_tasks = load_completed_tasks()
    if completed_tasks:
        print("\n已完成的任务列表:")
        print("=" * 80)
        for i, task in enumerate(sorted(completed_tasks), 1):
            keyword, city_code, start_date, end_date = task
            city_name = city.get(city_code, f"未知城市({city_code})")
            print(f"{i}. 关键词: {keyword} | 城市: {city_name}({city_code}) | 日期: {start_date} 至 {end_date}")
        print("=" * 80)
        print(f"共 {len(completed_tasks)} 个已完成任务\n")
    else:
        print("\n暂无已完成的任务\n")

def clear_completed_tasks():
    """清除已完成的任务记录"""
    if os.path.exists(PROGRESS_FILE):
        try:
            os.remove(PROGRESS_FILE)
            logger.info("已清除所有已完成的任务记录")
            print("已清除所有已完成的任务记录")
            return True
        except Exception as e:
            logger.error(f"清除任务记录失败: {e}")
            print(f"清除任务记录失败: {e}")
            return False
    else:
        print("没有任务记录文件可清除")
        return False


city = {
    1: "济南", 2: "贵阳", 3: "黔南", 4: "六盘水", 5: "南昌", 6: "九江", 7: "鹰潭", 8: "抚州",
    9: "上饶", 10: "赣州", 11: "重庆", 13: "包头", 14: "鄂尔多斯", 15: "巴彦淖尔", 16: "乌海",
    17: "阿拉善盟", 19: "锡林郭勒盟", 20: "呼和浩特", 21: "赤峰", 22: "通辽", 25: "呼伦贝尔",
    28: "武汉", 29: "大连", 30: "黄石", 31: "荆州", 32: "襄阳", 33: "黄冈", 34: "荆门",
    35: "宜昌", 36: "十堰", 37: "随州", 38: "恩施", 39: "鄂州", 40: "咸宁", 41: "孝感",
    42: "仙桃", 43: "长沙", 44: "岳阳", 45: "衡阳", 46: "株洲", 47: "湘潭", 48: "益阳",
    49: "郴州", 50: "福州", 51: "莆田", 52: "三明", 53: "龙岩", 54: "厦门", 55: "泉州",
    56: "漳州", 57: "上海", 59: "遵义", 61: "黔东南", 65: "湘西", 66: "娄底", 67: "怀化",
    68: "常德", 73: "天门", 74: "潜江", 76: "滨州", 77: "青岛", 78: "烟台", 79: "临沂",
    80: "潍坊", 81: "淄博", 82: "东营", 83: "聊城", 84: "菏泽", 85: "枣庄", 86: "德州",
    87: "宁德", 88: "威海", 89: "柳州", 90: "南宁", 91: "桂林", 92: "贺州", 93: "贵港",
    94: "深圳", 95: "广州", 96: "宜宾", 97: "成都", 98: "绵阳", 99: "广元", 100: "遂宁",
    101: "巴中", 102: "内江", 103: "泸州", 104: "南充", 106: "德阳", 107: "乐山", 108: "广安",
    109: "资阳", 111: "自贡", 112: "攀枝花", 113: "达州", 114: "雅安", 115: "吉安", 117: "昆明",
    118: "玉林", 119: "河池", 123: "玉溪", 124: "楚雄", 125: "南京", 126: "苏州", 127: "无锡",
    128: "北海", 129: "钦州", 130: "防城港", 131: "百色", 132: "梧州", 133: "东莞", 134: "丽水",
    135: "金华", 136: "萍乡", 137: "景德镇", 138: "杭州", 139: "西宁", 140: "银川", 141: "石家庄",
    143: "衡水", 144: "张家口", 145: "承德", 146: "秦皇岛", 147: "廊坊", 148: "沧州", 149: "温州",
    150: "沈阳", 151: "盘锦", 152: "哈尔滨", 153: "大庆", 154: "长春", 155: "四平", 156: "连云港",
    157: "淮安", 158: "扬州", 159: "泰州", 160: "盐城", 161: "徐州", 162: "常州", 163: "南通",
    164: "天津", 165: "西安", 166: "兰州", 168: "郑州", 169: "镇江", 172: "宿迁", 173: "铜陵",
    174: "黄山", 175: "池州", 176: "宣城", 177: "巢湖", 178: "淮南", 179: "宿州", 181: "六安",
    182: "滁州", 183: "淮北", 184: "阜阳", 185: "马鞍山", 186: "安庆", 187: "蚌埠", 188: "芜湖",
    189: "合肥", 191: "辽源", 194: "松原", 195: "云浮", 196: "佛山", 197: "湛江", 198: "江门",
    199: "惠州", 200: "珠海", 201: "韶关", 202: "阳江", 203: "茂名", 204: "潮州", 205: "揭阳",
    207: "中山", 208: "清远", 209: "肇庆", 210: "河源", 211: "梅州", 212: "汕头", 213: "汕尾",
    215: "鞍山", 216: "朝阳", 217: "锦州", 218: "铁岭", 219: "丹东", 220: "本溪", 221: "营口",
    222: "抚顺", 223: "阜新", 224: "辽阳", 225: "葫芦岛", 226: "张家界", 227: "大同", 228: "长治",
    229: "忻州", 230: "晋中", 231: "太原", 232: "临汾", 233: "运城", 234: "晋城", 235: "朔州",
    236: "阳泉", 237: "吕梁", 239: "海口", 241: "万宁", 242: "琼海", 243: "三亚", 244: "儋州",
    246: "新余", 253: "南平", 256: "宜春", 259: "保定", 261: "唐山", 262: "南阳", 263: "新乡",
    264: "开封", 265: "焦作", 266: "平顶山", 268: "许昌", 269: "永州", 270: "吉林", 271: "铜川",
    272: "安康", 273: "宝鸡", 274: "商洛", 275: "渭南", 276: "汉中", 277: "咸阳", 278: "榆林",
    280: "石河子", 281: "庆阳", 282: "定西", 283: "武威", 284: "酒泉", 285: "张掖", 286: "嘉峪关",
    287: "台州", 288: "衢州", 289: "宁波", 291: "眉山", 292: "邯郸", 293: "邢台", 295: "伊春",
    297: "大兴安岭", 300: "黑河", 301: "鹤岗", 302: "七台河", 303: "绍兴", 304: "嘉兴", 305: "湖州",
    306: "舟山", 307: "平凉", 308: "天水", 309: "白银", 310: "吐鲁番", 311: "昌吉", 312: "哈密",
    315: "阿克苏", 317: "克拉玛依", 318: "博尔塔拉", 319: "齐齐哈尔", 320: "佳木斯", 322: "牡丹江",
    323: "鸡西", 324: "绥化", 331: "乌兰察布", 333: "兴安盟", 334: "大理", 335: "昭通", 337: "红河",
    339: "曲靖", 342: "丽江", 343: "金昌", 344: "陇南", 346: "临夏", 350: "临沧", 352: "济宁",
    353: "泰安", 356: "莱芜", 359: "双鸭山", 366: "日照", 370: "安阳", 371: "驻马店", 373: "信阳",
    374: "鹤壁", 375: "周口", 376: "商丘", 378: "洛阳", 379: "漯河", 380: "濮阳", 381: "三门峡",
    383: "阿勒泰", 384: "喀什", 386: "和田", 391: "亳州", 395: "吴忠", 396: "固原", 401: "延安",
    405: "邵阳", 407: "通化", 408: "白山", 410: "白城", 417: "甘孜", 422: "铜仁", 424: "安顺",
    426: "毕节", 437: "文山", 438: "保山", 456: "东方", 457: "阿坝", 466: "拉萨", 467: "乌鲁木齐",
    472: "石嘴山", 479: "凉山", 480: "中卫", 499: "巴音郭楞", 506: "来宾", 514: "北京", 516: "日喀则",
    520: "伊犁", 525: "延边", 563: "塔城", 582: "五指山", 588: "黔西南", 608: "海西", 652: "海东",
    653: "克孜勒苏柯尔克孜", 654: "天门仙桃", 655: "那曲", 656: "林芝", 657: "None", 658: "防城",
    659: "玉树", 660: "伊犁哈萨克", 661: "五家渠", 662: "思茅", 663: "香港", 664: "澳门", 665: "崇左",
    666: "普洱", 667: "济源", 668: "西双版纳", 669: "德宏", 670: "文昌", 671: "怒江", 672: "迪庆",
    673: "甘南", 674: "陵水黎族自治县", 675: "澄迈县", 676: "海南", 677: "山南", 678: "昌都",
    679: "乐东黎族自治县", 680: "临高县", 681: "定安县", 682: "海北", 683: "昌江黎族自治县",
    684: "屯昌县", 685: "黄南", 686: "保亭黎族苗族自治县", 687: "神农架", 688: "果洛",
    689: "白沙黎族自治县", 690: "琼中黎族苗族自治县", 691: "阿里", 692: "阿拉尔", 693: "图木舒克"
}


def decrypt(key, data):
    """解密百度指数数据"""
    if not key or not data:
        return ""
    
    i = list(key)
    n = list(data)
    a = {}
    r = []
    
    # 构建映射字典
    for A in range(len(i) // 2):
        a[i[A]] = i[len(i) // 2 + A]
    
    # 根据映射解密数据
    for o in range(len(n)):
        r.append(a.get(n[o], n[o]))
    
    return ''.join(r)


def get_cipher_text(keyword):
    """获取Cipher-Text参数"""
    try:
        with open('single/Cipher-Text.js', 'r', encoding='utf-8') as f:
            js = f.read()
            ctx = execjs.compile(js)
        encoded_keyword = urllib.parse.quote(keyword)
        url_cipher = f'https://index.baidu.com/v2/main/index.html#/trend/{encoded_keyword}?words={encoded_keyword}'
        cipher_text = ctx.call('ascToken', url_cipher)
        return cipher_text
    except Exception as e:
        print(f"生成Cipher-Text失败: {e}")
        return None


def get_key(uniqid, cookies):
    """获取解密密钥"""
    try:
        params = {'uniqid': uniqid}
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
        response = requests.get(
            'https://index.baidu.com/Interface/ptbk',
            params=params,
            cookies=cookies,
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"获取解密密钥失败: {response.status_code}")
            return None
        
        data = response.json()
        if data.get('status') != 0:
            print(f"获取解密密钥失败: {data}")
            return None
        
        return data.get('data')
    except Exception as e:
        print(f"获取解密密钥出错: {e}")
        return None


def get_data(city_number, word, start_date, end_date):
    """请求接口获取数据"""
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
    
    # 构建word参数
    word_param = json.dumps([[{"name": word, "wordType": 1}]], ensure_ascii=False)
    encoded_word = urllib.parse.quote(word_param)
    
    # 构建请求URL
    url = f'https://index.baidu.com/api/SearchApi/index?area={city_number}&word={encoded_word}&startDate={start_date}&endDate={end_date}'
    
    # 获取Cipher-Text
    cipher_text = get_cipher_text(word)
    if not cipher_text:
        print(f"获取Cipher-Text失败，跳过请求")
        return None
    
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Cipher-Text': cipher_text,
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
    
    # 发送请求获取数据
    try:
        response = requests.get(url, cookies=cookies, headers=headers, timeout=30)
        time.sleep(1)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"请求出错: {e}")
        return None


def process_data(data, keyword, city_code, city_name, start_date, end_date):
    """
    处理搜索指数数据，返回日度/周度数据和年度统计数据
    """
    import json
    
    if not data or not data.get('data'):
        print(f"数据为空或格式不正确")
        return [], None
    
    try:
        # 获取uniqid用于解密
        uniqid = data['data'].get('uniqid')
        if not uniqid:
            print(f"缺少uniqid字段")
            return [], None
        
        # 获取解密密钥
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
        key = get_key(uniqid, cookies)
        if not key:
            print(f"获取解密密钥失败")
            return [], None
        
        # 获取用户指数数据
        user_indexes = data['data'].get('userIndexes', [])
        if not user_indexes or len(user_indexes) == 0:
            print(f"缺少userIndexes数据")
            return [], None
        
        user_index = user_indexes[0]
        all_data = user_index.get('all', {}).get('data', '')
        wise_data = user_index.get('wise', {}).get('data', '')
        pc_data = user_index.get('pc', {}).get('data', '')
        
        # 解密数据
        decrypted_all = decrypt(key, all_data)
        decrypted_wise = decrypt(key, wise_data)
        decrypted_pc = decrypt(key, pc_data)
        
        # 计算日期范围
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        total_days = (end - start).days + 1
        
        # 判断数据间隔：如果小于等于一年，间隔为1天（日度），否则为7天（周度）
        if total_days <= 365:
            interval = 1
            data_type = '日度'
        else:
            interval = 7
            data_type = '周度'
        
        # 处理日度/周度数据
        all_values = decrypted_all.split(',') if decrypted_all else []
        wise_values = decrypted_wise.split(',') if decrypted_wise else []
        pc_values = decrypted_pc.split(',') if decrypted_pc else []
        
        # 确保数据长度一致
        max_length = max(len(all_values), len(wise_values), len(pc_values))
        if len(all_values) < max_length:
            all_values.extend(['0'] * (max_length - len(all_values)))
        if len(wise_values) < max_length:
            wise_values.extend(['0'] * (max_length - len(wise_values)))
        if len(pc_values) < max_length:
            pc_values.extend(['0'] * (max_length - len(pc_values)))
        
        # 生成日期列表
        daily_data = []
        for i in range(max_length):
            current_date = (start + timedelta(days=i * interval))
            # 如果日期超过结束日期，停止
            if current_date > end:
                break
            
            date_str = current_date.strftime('%Y-%m-%d')
            year = date_str[:4]
            
            daily_record = {
                '关键词': keyword,
                '城市代码': city_code,
                '城市': city_name,
                '日期': date_str,
                '数据类型': data_type,
                '数据间隔(天)': interval,
                '所属年份': year,
                'PC+移动指数': all_values[i] if i < len(all_values) else '0',
                '移动指数': wise_values[i] if i < len(wise_values) else '0',
                'PC指数': pc_values[i] if i < len(pc_values) else '0',
                '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            daily_data.append(daily_record)
        
        # 处理年度统计数据
        general_ratio = data['data'].get('generalRatio', [])
        stats_record = None
        
        if general_ratio and len(general_ratio) > 0:
            ratio_data = general_ratio[0]
            all_stats = ratio_data.get('all', {})
            wise_stats = ratio_data.get('wise', {})
            pc_stats = ratio_data.get('pc', {})
            
            # 计算总值
            all_total = sum(int(v) for v in all_values if v.isdigit())
            wise_total = sum(int(v) for v in wise_values if v.isdigit())
            pc_total = sum(int(v) for v in pc_values if v.isdigit())
            
            stats_record = {
                '关键词': keyword,
                '城市代码': city_code,
                '城市': city_name,
                '时间范围': f"{start_date} 至 {end_date}",
                '整体日均值': all_stats.get('avg', 0),
                '整体同比': all_stats.get('yoy', '-'),
                '整体环比': all_stats.get('qoq', '-'),
                '移动日均值': wise_stats.get('avg', 0),
                '移动同比': wise_stats.get('yoy', '-'),
                '移动环比': wise_stats.get('qoq', '-'),
                'PC日均值': pc_stats.get('avg', 0),
                'PC同比': pc_stats.get('yoy', '-'),
                'PC环比': pc_stats.get('qoq', '-'),
                '整体总值': all_total,
                '移动总值': wise_total,
                'PC总值': pc_total,
                '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        return daily_data, stats_record
        
    except Exception as e:
        print(f"处理数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return [], None


if __name__ == "__main__":
    # 自定义输入
    print("=" * 50)
    print("百度指数数据爬取工具")
    print("=" * 50)
    
    # 询问是否查看已完成的任务
    view_completed = input("是否查看已完成的任务列表？(y/n，默认n): ").strip().lower()
    if view_completed == 'y':
        print_completed_tasks()
        clear_choice = input("是否清除已完成的任务记录（重新爬取）？(y/n，默认n): ").strip().lower()
        if clear_choice == 'y':
            confirm = input("确认清除所有已完成的任务记录？(y/n): ").strip().lower()
            if confirm == 'y':
                clear_completed_tasks()
            else:
                print("已取消清除操作")
        continue_choice = input("是否继续爬取？(y/n，默认y): ").strip().lower()
        if continue_choice == 'n':
            print("程序退出")
            exit(0)
    
    # 输入关键词
    keyword = input("请输入关键词（例如：智能手机）: ").strip()
    if not keyword:
        print("关键词不能为空！")
        exit(1)
    
    # 输入开始日期
    start_date = input("请输入开始日期（格式：YYYY-MM-DD，例如：2016-01-01）: ").strip()
    try:
        datetime.strptime(start_date, '%Y-%m-%d')
    except ValueError:
        print("开始日期格式错误！")
        exit(1)
    
    # 输入结束日期
    end_date = input("请输入结束日期（格式：YYYY-MM-DD，例如：2024-12-31）: ").strip()
    try:
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        print("结束日期格式错误！")
        exit(1)
    
    # 如果结束日期超过今天，使用今天作为结束日期
    today = datetime.now()
    if end_datetime > today:
        end_date = today.strftime('%Y-%m-%d')
        print(f"结束日期超过今天，已自动调整为: {end_date}")
    
    # 输入城市代码（可选，默认使用所有城市）
    city_input = input("请输入城市代码（留空则爬取所有城市，多个城市用逗号分隔）: ").strip()
    
    if city_input:
        # 解析城市代码
        city_codes = []
        for code_str in city_input.split(','):
            try:
                code = int(code_str.strip())
                if code in city:
                    city_codes.append(code)
                else:
                    print(f"警告: 城市代码 {code} 不存在，已跳过")
            except ValueError:
                print(f"警告: '{code_str}' 不是有效的城市代码，已跳过")
        
        if not city_codes:
            print("没有有效的城市代码，将爬取所有城市")
            city_codes = list(city.keys())
    else:
        city_codes = list(city.keys())
    
    print(f"\n开始爬取数据...")
    print(f"关键词: {keyword}")
    print(f"日期范围: {start_date} 至 {end_date}")
    print(f"城市数量: {len(city_codes)}")
    print("=" * 50)
    
    # 存储所有数据
    all_daily_data = []
    all_stats_data = []
    
    # 加载已完成的任务
    completed_tasks = load_completed_tasks()
    logger.info(f"已加载 {len(completed_tasks)} 个已完成任务")
    
    # 显示已完成的任务
    if completed_tasks:
        print("\n检测到已完成的任务，将自动跳过:")
        print_completed_tasks()
    
    # 遍历城市
    total_cities = len(city_codes)
    completed_count = 0
    skipped_count = 0
    
    for idx, city_code in enumerate(city_codes, 1):
        city_name = city[city_code]
        
        # 检查任务是否已完成
        if is_task_completed(keyword, city_code, start_date, end_date):
            skipped_count += 1
            logger.info(f"[{idx}/{total_cities}] 跳过已完成任务: {city_name}({city_code})")
            print(f"[{idx}/{total_cities}] 跳过已完成任务: {city_name}({city_code})")
            continue
        
        print(f"\n[{idx}/{total_cities}] 正在爬取 {city_name}({city_code}) 的数据...")
        logger.info(f"[{idx}/{total_cities}] 开始爬取: {keyword} - {city_name}({city_code}) - {start_date}至{end_date}")
        
        try:
            # 获取数据
            data = get_data(city_code, keyword, start_date, end_date)
            
            if not data:
                print(f"  {city_name} 数据获取失败")
                logger.warning(f"{city_name} 数据获取失败")
                continue
            
            # 检查响应状态
            if data.get('status') != 0:
                print(f"  {city_name} API返回错误: {data.get('status')}")
                logger.warning(f"{city_name} API返回错误: {data.get('status')}")
                continue
            
            # 处理数据
            daily_data, stats_record = process_data(data, keyword, city_code, city_name, start_date, end_date)
            
            if daily_data:
                all_daily_data.extend(daily_data)
                print(f"  {city_name} 日度/周度数据: {len(daily_data)} 条")
                logger.info(f"{city_name} 日度/周度数据: {len(daily_data)} 条")
            
            if stats_record:
                all_stats_data.append(stats_record)
                print(f"  {city_name} 统计数据已获取")
                logger.info(f"{city_name} 统计数据已获取")
            
            # 保存任务完成状态
            save_completed_task(keyword, city_code, start_date, end_date)
            completed_count += 1
            logger.info(f"{city_name} 任务完成并保存")
            
        except KeyboardInterrupt:
            logger.warning("用户中断程序")
            print("\n\n程序被用户中断！")
            print(f"已完成: {completed_count} 个任务")
            print(f"跳过: {skipped_count} 个已完成任务")
            print(f"剩余: {total_cities - completed_count - skipped_count} 个任务")
            print("\n已完成的任务已保存，下次运行将自动跳过这些任务")
            print_completed_tasks()
            raise
        except Exception as e:
            print(f"  {city_name} 处理出错: {e}")
            logger.error(f"{city_name} 处理出错: {e}", exc_info=True)
            import traceback
            traceback.print_exc()
            continue
    
    # 打印统计信息
    print("\n" + "=" * 50)
    print("任务统计:")
    print(f"  总任务数: {total_cities}")
    print(f"  已完成: {completed_count}")
    print(f"  跳过(已完成): {skipped_count}")
    print(f"  失败: {total_cities - completed_count - skipped_count}")
    logger.info(f"任务统计 - 总数: {total_cities}, 完成: {completed_count}, 跳过: {skipped_count}")
    
    # 保存数据
    print("\n" + "=" * 50)
    print("保存数据...")
    
    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    daily_file = f"百度指数_日度周度数据_{keyword}_{timestamp}.csv"
    stats_file = f"百度指数_年度统计数据_{keyword}_{timestamp}.csv"
    
    # 保存日度/周度数据
    if all_daily_data:
        daily_df = pd.DataFrame(all_daily_data)
        daily_df.to_csv(daily_file, index=False, encoding='utf-8-sig')
        print(f"日度/周度数据已保存到: {daily_file}")
        print(f"  共 {len(all_daily_data)} 条记录")
    else:
        print("没有日度/周度数据可保存")
    
    # 保存年度统计数据
    if all_stats_data:
        stats_df = pd.DataFrame(all_stats_data)
        stats_df.to_csv(stats_file, index=False, encoding='utf-8-sig')
        print(f"年度统计数据已保存到: {stats_file}")
        print(f"  共 {len(all_stats_data)} 条记录")
    else:
        print("没有年度统计数据可保存")
    
    print("\n爬取完成！")
    logger.info("所有任务完成")
    
    # 最后显示已完成的任务列表
    print("\n最终已完成的任务列表:")
    print_completed_tasks()
