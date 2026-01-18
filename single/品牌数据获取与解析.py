"""
百度指数 - 品牌指数爬虫
使用新的品牌指数API接口，支持自定义区域爬取
"""
import requests
import pandas as pd
from datetime import datetime
import os
import time
import json


# ==================== Cookie 配置 ====================
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

# ==================== 配置区域 ====================
# 关键词列表（可以自定义修改）
KEYWORDS = [
    "岩寺新四军军部旧址",
    "柯村",
    "皖西烈士陵园",
    "藕塘烈士纪念馆",
    "金寨革命烈士陵园",
    # 在这里添加更多关键词
]

# 城市列表（可以自定义修改，支持省份和城市名称）
CITIES = [
    "安徽"
    # 在这里添加更多城市或省份
]

# 日期范围（格式：YYYY-MM-DD）
START_DATE = "2021-12-01"
END_DATE = "2026-01-16"

# 请求间隔（秒），避免请求过快被封
REQUEST_DELAY = 1

# ==================== 请求头配置 ====================
headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://index.baidu.com",
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

# 省份映射（省份名称 -> region_id）
provinces = {
    "北京": 1,
    "上海": 2,
    "天津": 3,
    "广东": 4,
    "福建": 5,
    "海南": 8,
    "安徽": 9,
    "贵州": 10,
    "甘肃": 11,
    "广西": 12,
    "河北": 13,
    "河南": 14,
    "黑龙江": 15,
    "湖北": 16,
    "湖南": 17,
    "吉林": 18,
    "江苏": 19,
    "江西": 20,
    "辽宁": 21,
    "内蒙古": 22,
    "宁夏": 23,
    "青海": 24,
    "山东": 25,
    "山西": 26,
    "陕西": 27,
    "四川": 28,
    "西藏": 29,
    "新疆": 30,
    "云南": 31,
    "浙江": 32,
    "重庆": 33,
    "香港": 34,
    "台湾": 35,
    "澳门": 36
}

# 城市映射（城市名称 -> region_id）
cityShip = {
    # 广东省城市
    "江门": 82, "揭阳": 83, "广州": 84, "潮州": 85, "茂名": 86, "梅州": 88,
    "清远": 89, "佛山": 90, "汕头": 91, "汕尾": 92, "深圳": 93, "韶关": 94,
    "阳江": 109, "湛江": 110, "云浮": 111, "中山": 112, "珠海": 113, "肇庆": 114,
    "河源": 115, "东莞": 116, "惠州": 117,
    # 福建省城市
    "莆田": 48, "南平": 49, "龙岩": 50, "宁德": 51, "泉州": 52, "三明": 66,
    "厦门": 70, "漳州": 80, "福州": 81,
    # 海南省城市
    "东方": 296, "琼海": 297, "三亚": 298, "文昌": 299, "五指山": 300, "万宁": 301,
    "海口": 302, "儋州": 303,
    # 安徽省城市
    "淮北": 127, "安庆": 128, "巢湖": 129, "池州": 130, "滁州": 131, "黄山": 132,
    "淮南": 133, "马鞍山": 134, "六安": 135, "宣城": 136, "宿州": 137, "铜陵": 138,
    "芜湖": 139, "阜阳": 140, "蚌埠": 141, "合肥": 142, "亳州": 143,
    # 贵州省城市
    "贵阳": 118, "安顺": 119, "六盘水": 120, "黔南": 121, "黔东南": 122,
    "黔西南": 123, "毕节": 124, "铜仁": 125, "遵义": 126,
    # 甘肃省城市
    "酒泉": 255, "金昌": 256, "嘉峪关": 257, "兰州": 258, "陇南": 259, "平凉": 260,
    "临夏": 261, "庆阳": 262, "定西": 263, "武威": 264, "天水": 265, "张掖": 266,
    "白银": 267, "甘南": 477,
    # 广西省城市
    "桂林": 95, "贵港": 96, "防城港": 98, "南宁": 99, "来宾": 100, "柳州": 101,
    "钦州": 102, "梧州": 103, "北海": 104, "玉林": 105, "河池": 106, "贺州": 107,
    "百色": 108, "崇左": 478,
    # 河北省城市
    "保定": 304, "沧州": 305, "承德": 306, "廊坊": 307, "秦皇岛": 325, "邢台": 326,
    "石家庄": 327, "唐山": 329, "邯郸": 330, "张家口": 331, "衡水": 332,
    # 河南省城市
    "焦作": 308, "安阳": 309, "开封": 310, "洛阳": 311, "漯河": 312, "平顶山": 313,
    "驻马店": 314, "南阳": 315, "濮阳": 316, "新乡": 317, "信阳": 318, "许昌": 319,
    "商丘": 320, "三门峡": 321, "郑州": 322, "鹤壁": 323, "周口": 324, "济源": 476,
    # 黑龙江省城市
    "鸡西": 333, "佳木斯": 334, "哈尔滨": 335, "牡丹江": 336, "齐齐哈尔": 337,
    "七台河": 338, "绥化": 339, "双鸭山": 340, "伊春": 341, "大庆": 342,
    "大兴安岭": 343, "鹤岗": 344, "黑河": 345,
    # 湖北省城市
    "荆门": 346, "荆州": 347, "黄石": 348, "黄冈": 349, "潜江": 364, "孝感": 365,
    "恩施": 366, "随州": 367, "神农架": 368, "十堰": 369, "襄阳": 370, "武汉": 371,
    "仙桃": 372, "天门": 373, "咸宁": 375, "宜昌": 376, "鄂州": 377,
    # 湖南省城市
    "怀化": 350, "常德": 351, "长沙": 352, "郴州": 353, "娄底": 354, "邵阳": 355,
    "湘潭": 356, "湘西": 357, "张家界": 358, "益阳": 359, "衡阳": 360, "岳阳": 361,
    "永州": 362, "株洲": 363,
    # 吉林省城市
    "吉林": 38, "白城": 39, "长春": 40, "辽源": 41, "白山": 42, "四平": 43,
    "松原": 44, "通化": 45, "延吉": 46, "延边": 47,
    # 江苏省城市
    "淮安": 53, "常州": 54, "南京": 55, "南通": 56, "连云港": 57, "徐州": 58,
    "苏州": 59, "宿迁": 60, "泰州": 61, "无锡": 62, "盐城": 63, "扬州": 64, "镇江": 65,
    # 江西省城市
    "九江": 67, "吉安": 68, "景德镇": 69, "萍乡": 71, "南昌": 72, "新余": 73,
    "上饶": 74, "宜春": 75, "鹰潭": 76, "赣州": 77, "抚州": 78,
    # 辽宁省城市
    "丹东": 144, "本溪": 145, "锦州": 146, "朝阳": 147, "辽阳": 148, "盘锦": 149,
    "阜新": 150, "鞍山": 151, "抚顺": 152, "沈阳": 153, "铁岭": 154, "大连": 155,
    "营口": 156, "葫芦岛": 157,
    # 内蒙古城市
    "赤峰": 158, "阿拉善盟": 159, "兴安盟": 160, "通辽": 161, "巴彦淖尔": 162,
    "乌兰察布": 163, "乌海": 164, "锡林郭勒盟": 165, "呼伦贝尔": 166, "呼和浩特": 167,
    "鄂尔多斯": 168, "包头": 169,
    # 宁夏城市
    "固原": 170, "石嘴山": 171, "吴忠": 172, "中卫": 173, "银川": 174,
    # 青海省城市
    "西宁": 175, "海东": 176, "海西": 177, "玉树": 178, "海南": 479, "海北": 494,
    "黄南": 495, "果洛": 496,
    # 山东省城市
    "济南": 196, "济宁": 197, "莱芜": 198, "聊城": 199, "德州": 200, "临沂": 201,
    "青岛": 202, "日照": 203, "潍坊": 204, "淄博": 207, "泰安": 208, "威海": 218,
    "烟台": 219, "东营": 220, "枣庄": 221, "菏泽": 222, "滨州": 223,
    # 山西省城市
    "晋城": 205, "晋中": 206, "长治": 209, "吕梁": 210, "临汾": 211, "忻州": 212,
    "朔州": 213, "太原": 214, "阳泉": 215, "运城": 216, "大同": 217,
    # 陕西省城市
    "宝鸡": 239, "安康": 240, "商洛": 241, "铜川": 242, "渭南": 243, "西安": 244,
    "咸阳": 245, "延安": 246, "汉中": 248, "榆林": 249,
    # 四川省城市
    "广安": 224, "广元": 225, "成都": 226, "眉山": 227, "凉山": 228, "绵阳": 229,
    "攀枝花": 230, "南充": 231, "德阳": 232, "乐山": 233, "泸州": 234, "内江": 235,
    "甘孜": 236, "遂宁": 237, "资阳": 238, "巴中": 247, "达州": 250, "雅安": 251,
    "阿坝": 252, "自贡": 253, "宜宾": 254,
    # 西藏城市
    "那曲": 268, "拉萨": 269, "林芝": 270, "日喀则": 271, "昌都": 480, "山南": 497, "阿里": 498,
    # 新疆城市
    "哈密": 179, "博尔塔拉": 180, "昌吉": 181, "阿勒泰": 182, "喀什": 183, "克拉玛依": 184,
    "阿克苏": 185, "克孜勒苏柯尔克孜": 186, "石河子": 187, "塔城": 188, "五家渠": 189,
    "吐鲁番": 190, "巴音郭楞": 191, "乌鲁木齐": 192, "伊犁": 193, "和田": 195,
    "阿拉尔": 499, "图木舒克": 500,
    # 云南省城市
    "楚雄": 283, "昆明": 284, "丽江": 285, "德宏": 286, "临沧": 287, "曲靖": 288,
    "保山": 289, "普洱": 290, "文山": 291, "大理": 292, "红河": 293, "昭通": 294,
    "玉溪": 295, "怒江": 481, "迪庆": 482, "西双版纳": 483,
    # 浙江省城市
    "金华": 272, "嘉兴": 273, "衢州": 274, "丽水": 275, "宁波": 276, "绍兴": 277,
    "温州": 278, "台州": 279, "杭州": 280, "舟山": 281, "湖州": 282,
}
# 输出目录
OUTPUT_DIR = "output"


def get_brand_info_id(keyword):
    """
    通过关键词获取品牌信息ID
    
    Args:
        keyword: 关键词
    
    Returns:
        brandInfo中的id，如果获取失败返回None
    """
    url = "https://index.baidu.com/insight/word/sug"
    data = {
        "words": [keyword],
        "source": "pc_landpage_comp"
    }
    data_json = json.dumps(data, separators=(',', ':'))
    
    try:
        response = requests.post(url, headers=headers, cookies=cookies, data=data_json)
        response.raise_for_status()
        
        result = response.json()
        if result.get('status') == 0:
            data_obj = result.get('data', {})
            result_list = data_obj.get('result', [])
            if result_list and len(result_list) > 0:
                brand_info = result_list[0].get('brandInfo', {})
                if brand_info:
                    return brand_info.get('id')
        
        print(f"警告: 无法获取关键词 '{keyword}' 的品牌ID")
        return None
    except Exception as e:
        print(f"获取关键词 '{keyword}' 的品牌ID时发生错误: {str(e)}")
        return None


def fetch_brand_index(entity_id, region_id, start_date, end_date):
    """
    获取品牌指数数据
    
    Args:
        entity_id: 品牌实体ID
        region_id: 地区ID
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        API返回的JSON数据
    """
    url = "https://index.baidu.com/insight/brand/queryBrandIndex"
    data = {
        "entityId": entity_id,
        "regionId": region_id,
        "stat": True,
        "startDate": start_date,
        "endDate": end_date
    }
    data_json = json.dumps(data, separators=(',', ':'))
    
    try:
        response = requests.post(url, headers=headers, cookies=cookies, data=data_json)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"请求品牌指数数据时发生错误: {str(e)}")
        return {"status": -1, "message": str(e)}

def get_region_id_by_name(name):
    """
    根据地区名称获取region_id
    
    Args:
        name: 地区名称（省份或城市）
    
    Returns:
        region_id，如果找不到返回None
    """
    # 首先检查是否是省份
    if name in provinces:
        return provinces[name]
    
    # 然后检查是否是城市
    if name in cityShip:
        return cityShip[name]
    
    return None

def get_region_name(region_id):
    """根据地区ID获取地区名称"""
    # 首先检查是否是省份（反向查找）
    for province_name, province_id in provinces.items():
        if province_id == region_id:
            return province_name
    
    # 然后检查是否是城市
    for city_name, city_id in cityShip.items():
        if city_id == region_id:
            return city_name
    
    return f"未知地区({region_id})"

def parse_and_save(response_data, keyword, region_id, start_date, end_date, is_first=True):
    """
    解析数据并追加到CSV文件
    
    Args:
        response_data: API返回的JSON数据
        keyword: 关键词/品牌名称
        region_id: 地区ID
        start_date: 开始日期
        end_date: 结束日期
        is_first: 是否是第一次写入（用于决定是否写入表头）
    
    Returns:
        rows: 数据行列表
    """
    if response_data.get('status') != 0:
        print(f"请求失败: {response_data}")
        return []
    
    data_list = response_data.get('data', [])
    if not data_list:
        print("没有获取到数据")
        return []
    
    # 获取当前爬取时间
    crawl_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 获取城市名称
    city_name = get_region_name(region_id)
    
    # 数据类型
    data_type = "日度"
    
    # 数据间隔（天）- 品牌指数API返回的是日度数据，间隔为1天
    data_interval = 1
    
    # 准备数据列表
    rows = []
    for item in data_list:
        stat_date = item.get('statDate', '')
        value = item.get('value', 0)
        
        # 提取年份
        year = stat_date.split('-')[0] if stat_date else ''
        
        # 构建一行数据
        rows.append({
            '关键词': keyword,
            '城市': city_name,
            '日期': stat_date,
            '数据类型': data_type,
            '数据间隔(天)': data_interval,
            '所属年份': year,
            '值': value,
            '爬取时间': crawl_time
        })
    
    print(f"解析到 {len(rows)} 条记录")
    
    # 打印统计信息
    stat = response_data.get('stat', {})
    if stat:
        print(f"统计信息: 平均值={stat.get('avg', 'N/A')}, 同比={stat.get('yearRatio', 'N/A')}%, 环比={stat.get('chainRatio', 'N/A')}%")
    
    return rows


def main():
    """主函数"""
    print("=" * 60)
    print("百度指数 - 品牌指数爬虫")
    print("=" * 60)
    print(f"关键词列表: {KEYWORDS}")
    print(f"城市列表: {CITIES}")
    print(f"日期范围: {START_DATE} ~ {END_DATE}")
    print("-" * 60)
    
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 构建统一的输出文件名
    output_file = os.path.join(OUTPUT_DIR, f"brand_index_{START_DATE}_{END_DATE}.csv")
    
    # 统计信息
    total_combinations = len(KEYWORDS) * len(CITIES)
    current_count = 0
    success_count = 0
    fail_count = 0
    
    # 收集所有数据
    all_rows = []
    
    # 遍历所有关键词和城市的组合
    for keyword in KEYWORDS:
        print(f"\n{'='*60}")
        print(f"处理关键词: {keyword}")
        print(f"{'='*60}")
        
        # 获取关键词的品牌ID
        print(f"正在获取关键词 '{keyword}' 的品牌ID...")
        entity_id = get_brand_info_id(keyword)
        
        if not entity_id:
            print(f"跳过关键词 '{keyword}'，无法获取品牌ID")
            fail_count += len(CITIES)
            current_count += len(CITIES)
            continue
        
        print(f"关键词 '{keyword}' 的品牌ID: {entity_id}")
        
        # 遍历所有城市
        for city_name in CITIES:
            current_count += 1
            print(f"\n[{current_count}/{total_combinations}] 处理城市: {city_name}")
            
            # 获取城市的region_id
            region_id = get_region_id_by_name(city_name)
            if not region_id:
                print(f"警告: 无法找到城市 '{city_name}' 的region_id，跳过")
                fail_count += 1
                continue
            
            print(f"城市 '{city_name}' 的region_id: {region_id}")
            
            try:
                # 获取数据
                print(f"正在获取数据...")
                response_data = fetch_brand_index(entity_id, region_id, START_DATE, END_DATE)
                
                # 解析数据
                if response_data.get('status') == 0:
                    rows = parse_and_save(response_data, keyword, region_id, START_DATE, END_DATE)
                    if rows:
                        all_rows.extend(rows)
                        success_count += 1
                        print(f"✓ 成功获取数据")
                    else:
                        fail_count += 1
                else:
                    print(f"✗ 获取数据失败: {response_data.get('message', '未知错误')}")
                    fail_count += 1
                
                # 请求间隔，避免请求过快
                if current_count < total_combinations:
                    time.sleep(REQUEST_DELAY)
                    
            except Exception as e:
                print(f"✗ 处理时发生错误: {str(e)}")
                fail_count += 1
                import traceback
                traceback.print_exc()
    
    # 保存所有数据到一个CSV文件
    if all_rows:
        df = pd.DataFrame(all_rows)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n数据已保存到: {output_file}")
        print(f"共保存 {len(all_rows)} 条记录")
    else:
        print("\n没有获取到任何数据")
    
    # 打印最终统计
    print(f"\n{'='*60}")
    print("爬取完成！")
    print(f"{'='*60}")
    print(f"总组合数: {total_combinations}")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
