import requests
import time
import pandas as pd
from datetime import datetime
import json
import os
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from functools import wraps
from fake_useragent import UserAgent
import execjs
ua = UserAgent()
useragent=ua.random#随机生成谷歌浏览器的useragent，想要各种浏览器的改chrome为randome


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 配置参数
CONFIG = {
    'batch_size': 100,  # 每批次保存的记录数
    'max_workers': 6,  # 并发线程数
    'retry_times': 3,  # 重试次数
    'base_delay': 1,  # 基础延迟时间（秒）
    'max_delay': 1.5,    # 最大延迟时间（秒）
    'progress_file': 'crawler_progress.json',  # 进度文件
    'output_dir': 'data_batches',  # 批次数据目录
    'final_output': '百度指数_全部关键词.xlsx',  # 最终输出文件
    'use_local_ip': True  # 是否使用本地IP
}


# 线程锁
progress_lock = threading.Lock()
batch_lock = threading.Lock()

# 全局变量
current_batch_data = []
processed_count = 0

# 重试装饰器
def retry(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"函数 {func.__name__} 重试 {max_retries} 次后仍然失败: {e}")
                        raise e
                    else:
                        wait_time = delay * (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}，等待 {wait_time:.2f} 秒后重试")
                        time.sleep(wait_time)
            return None
        return wrapper
    return decorator

# 进度管理类
class ProgressManager:
    def __init__(self, progress_file):
        self.progress_file = progress_file
        self.progress = self.load_progress()
    
    def load_progress(self):
        """加载进度"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                logger.warning("进度文件损坏，重新开始")
        return {}
    
    def save_progress(self):
        """保存进度"""
        with progress_lock:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, ensure_ascii=False, indent=2)
    
    def is_completed(self, word, city_number, year):
        """检查任务是否已完成"""
        key = f"{word}_{city_number}_{year}"
        return key in self.progress
    
    def mark_completed(self, word, city_number, year):
        """标记任务完成"""
        key = f"{word}_{city_number}_{year}"
        self.progress[key] = {
            'completed_at': datetime.now().isoformat(),
            'word': word,
            'city_number': city_number,
            'year': year
        }
        self.save_progress()

# 批次数据管理
class BatchManager:
    def __init__(self, output_dir, batch_size):
        self.output_dir = output_dir
        self.batch_size = batch_size
        self.current_batch = []
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 检查已有批次文件，确定起始批次号
        self.batch_count = self._get_max_batch_number()
        logger.info(f"批次管理初始化，从批次 {self.batch_count + 1} 开始")
    
    def _get_max_batch_number(self):
        """获取已有批次文件的最大批次号"""
        max_batch = 0
        if os.path.exists(self.output_dir):
            batch_files = []
            for file in os.listdir(self.output_dir):
                if file.startswith('batch_') and file.endswith('.xlsx'):
                    try:
                        # 从文件名提取批次号
                        batch_num = int(file.split('_')[1].split('.')[0])
                        batch_files.append(batch_num)
                    except:
                        pass
            
            if batch_files:
                max_batch = max(batch_files)
                logger.info(f"检测到已有批次文件，最大批次号: {max_batch}")
        
        return max_batch
    
    def add_data(self, df):
        """添加数据到当前批次"""
        with batch_lock:
            self.current_batch.append(df)
            
            if len(self.current_batch) >= self.batch_size:
                self.save_current_batch()
    
    def save_current_batch(self):
        """保存当前批次数据"""
        if not self.current_batch:
            return
        
        try:
            combined_df = pd.concat(self.current_batch, ignore_index=True)
            self.batch_count += 1
            batch_file = os.path.join(self.output_dir, f'batch_{self.batch_count:04d}.xlsx')
            combined_df.to_excel(batch_file, index=False)
            
            logger.info(f"批次 {self.batch_count} 已保存，包含 {len(combined_df)} 条记录")
            self.current_batch = []
            
        except Exception as e:
            logger.error(f"保存批次数据失败: {e}")
    
    def save_final_batch(self):
        """保存最后一个批次"""
        if self.current_batch:
            # 强制保存当前批次，即使不满batch_size
            try:
                combined_df = pd.concat(self.current_batch, ignore_index=True)
                self.batch_count += 1
                batch_file = os.path.join(self.output_dir, f'batch_{self.batch_count:04d}.xlsx')
                combined_df.to_excel(batch_file, index=False)
                
                logger.info(f"最终批次 {self.batch_count} 已保存，包含 {len(combined_df)} 条记录")
                self.current_batch = []
                
            except Exception as e:
                logger.error(f"保存最终批次数据失败: {e}")
    
    def merge_all_batches(self, final_output):
        """合并所有批次文件"""
        try:
            batch_files = []
            for file in os.listdir(self.output_dir):
                if file.startswith('batch_') and file.endswith('.xlsx'):
                    batch_files.append(os.path.join(self.output_dir, file))
            
            if not batch_files:
                logger.warning("没有找到批次文件")
                return False
            
            # 按文件名排序
            batch_files.sort()
            
            all_data = []
            for batch_file in batch_files:
                try:
                    df = pd.read_excel(batch_file)
                    all_data.append(df)
                    logger.info(f"读取批次文件: {batch_file}, 记录数: {len(df)}")
                except Exception as e:
                    logger.error(f"读取批次文件失败 {batch_file}: {e}")
            
            if all_data:
                final_df = pd.concat(all_data, ignore_index=True)
                final_df.to_excel(final_output, index=False)
                logger.info(f"所有数据已合并保存到 {final_output}，总记录数: {len(final_df)}")
                return True
            
        except Exception as e:
            logger.error(f"合并批次文件失败: {e}")
            return False

# 请求频率控制
class RateLimiter:
    def __init__(self, min_delay=1, max_delay=1.5):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0
        self.lock = threading.Lock()
    
    def wait(self):
        """等待适当的时间间隔"""
        with self.lock:
            current_time = time.time()
            elapsed = current_time - self.last_request_time
            
            delay = random.uniform(self.min_delay, self.max_delay)
            if elapsed < delay:
                sleep_time = delay - elapsed
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()

# 全局速率限制器
rate_limiter = RateLimiter(CONFIG['base_delay'], CONFIG['max_delay'])

# 代理管理类
class ProxyManager:
    def __init__(self, proxy_list, use_local_ip=True):
        # 如果use_local_ip为True，则添加None作为本地IP选项
        self.proxy_list = proxy_list
        if use_local_ip:
            self.proxy_list.append(None)  # None表示使用本地IP
        self.current_index = 0
        self.lock = threading.Lock()
    
    def get_proxy(self):
        """获取一个代理"""
        with self.lock:
            proxy = self.proxy_list[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxy_list)
            return proxy

# 添加Cookie管理类
class CookieManager:
    def __init__(self, cookie_list):
        self.cookie_list = cookie_list
        self.current_index = 0
        self.lock = threading.Lock()
    
    def get_cookie(self):
        """获取一个Cookie"""
        with self.lock:
            cookie = self.cookie_list[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.cookie_list)
            return cookie

# 请求数据
@retry(max_retries=CONFIG['retry_times'])
def get_data(city_number, word, startDate, endDate, cookies, proxy_manager=None, cookie_manager=None):
    """获取百度指数数据"""
    # 频率控制
    rate_limiter.wait()
    
    # 如果提供了cookie_manager，则使用它来获取cookie
    if cookie_manager:
        cookies = cookie_manager.get_cookie()
    
    # 构建请求URL
    url = f'https://index.baidu.com/api/SearchApi/index?area={city_number}&word=[[{{"name":"{word}","wordType":1}}]]&startDate={startDate}&endDate={endDate}'
    
    url_cipyter = f'https://index.baidu.com/v2/main/index.html#/trend/{word}?words={word}'

    with open('Cipher-Text.js', 'r') as f:
        js = f.read()
        ctx = execjs.compile(js)
    cipyer_text=ctx.call('ascToken',url_cipyter)
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
    }
    
    # 获取代理配置
    proxies = None
    if proxy_manager:
        proxies = proxy_manager.get_proxy()
        
    # 记录当前使用的代理和cookie
    # proxy_info = "本地IP" if proxies is None else str(proxies)
    # logger.info(f"请求 {word} - {city_number} - {startDate} 使用代理: {proxy_info}")

    # 发送请求
    response = requests.get(url, cookies=cookies, headers=headers, proxies=proxies, timeout=20)
    response.raise_for_status()  # 抛出HTTP错误
    
    return response.json()

# 分析数据
def analyze_data(data, city_number, city_name, word, year):
    """分析百度指数数据"""
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
            '城市编号': [city_number],
            '年份': [year],
            '整体日均值': [generalRatio_all_avg],
            '移动日均值': [generalRatio_wise_avg],
            'PC日均值': [generalRatio_pc_avg],
            '整体年总值': [generalRatio_all_avg * days_in_year],
            '移动年总值': [generalRatio_wise_avg * days_in_year],
            'PC年总值': [generalRatio_pc_avg * days_in_year],
            '爬取时间': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        })
        
        return df
        
    except Exception as e:
        logger.error(f"数据解析错误: {e}, 原始数据: {data}")
        return pd.DataFrame()

# 处理单个任务
def process_single_task(task_info):
    """处理单个爬取任务"""
    word, city_number, city_name, year, progress_manager, batch_manager, proxy_manager, cookie_manager = task_info
    
    try:
        # 检查是否已完成
        if progress_manager.is_completed(word, city_number, year):
            logger.info(f"跳过已完成任务: {word} - {city_name} - {year}")
            return True
        
        # 构建日期
        startDate = f"{year}-01-01"
        endDate = f"{year}-12-31"
        if year == 2025:
            endDate = "2025-06-23"
        
        logger.info(f"开始处理: {word} - {city_name} - {year}")
        
        # 获取数据，使用代理管理器和Cookie管理器
        data = get_data(city_number, word, startDate, endDate, None, proxy_manager, cookie_manager)
        
        # 分析数据
        df = analyze_data(data, city_number, city_name, word, year)
        
        if not df.empty:
            # 添加到批次管理器
            batch_manager.add_data(df)
            
            # 标记完成
            progress_manager.mark_completed(word, city_number, year)
            
            logger.info(f"完成处理: {word} - {city_name} - {year}")
            return True
        else:
            logger.warning(f"数据为空: {word} - {city_name} - {year}")
            return False
            
    except Exception as e:
        logger.error(f"处理任务失败: {word} - {city_name} - {year}, 错误: {e}")
        return False

def main():
    """主函数"""
    try:
        cookies_list = [{
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
        }]
        # 城市列表
        city = {
        1: "济南",
        2: "贵阳",
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
        39: "鄂州",
        40: "咸宁",
        41: "孝感",
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
        66: "娄底",
        67: "怀化",
        68: "常德",
        77: "青岛",
        78: "烟台",
        79: "临沂",
        80: "潍坊",
        81: "淄博",
        82: "东营",
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
        228: "长治",
        229: "忻州",
        230: "晋中",
        235: "朔州",
        236: "阳泉",
        237: "吕梁",
        239: "海口",
        243: "三亚",
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
        317: "克拉玛依",
        319: "齐齐哈尔",
        320: "佳木斯",
        322: "牡丹江",
        323: "鸡西",
        324: "绥化",
        335: "昭通",
        339: "曲靖",
        342: "丽江",
        343: "金昌",
        344: "陇南",
        350: "临沧",
        352: "济宁",
        353: "泰安",
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
        391: "亳州",
        395: "吴忠",
        396: "固原",
        401: "延安",
        405: "邵阳",
        407: "通化",
        408: "白山",
        422: "铜仁",
        424: "安顺",
        426: "毕节",
        438: "保山",
        466: "拉萨",
        467: "乌鲁木齐",
        472: "石嘴山",
        480: "中卫",
        506: "来宾",
        514: "北京",
        665: "崇左",
        666: "普洱",
    }

        
        # 读取关键词列表
        try:
            word_list = pd.read_excel('存在的数字设备和服务关键词.xlsx')
            keywords = word_list['关键词'].tolist()
            logger.info(f"成功读取到 {len(keywords)} 个关键词")
        except Exception as e:
            logger.error(f"读取关键词文件失败: {str(e)}")
            logger.info("使用默认关键词'数字政务APP'继续")
            keywords = ["数字政务APP"]
        
        years = list(range(2016, 2026))  # 2016年到2025年
        
        # 初始化管理器
        progress_manager = ProgressManager(CONFIG['progress_file'])
        batch_manager = BatchManager(CONFIG['output_dir'], CONFIG['batch_size'])
        
        # 构建代理管理器
        proxy_manager = ProxyManager([
            # {'http': 'http://15968588744:kwkdvtr6@61.184.8.27:10134', 'https': 'http://15968588744:kwkdvtr6@61.184.8.27:10134'},
            # {'http': 'http://15968588744:kwkdvtr6@110.166.229.165:16817', 'https': 'http://15968588744:kwkdvtr6@110.166.229.165:16817'},
        ], CONFIG['use_local_ip'])
        
        # 构建Cookie管理器
        cookie_manager = CookieManager(cookies_list)
        
        # 构建所有任务
        all_tasks = []
        for word in keywords:
            for year in years:
                for city_number, city_name in city.items():
                    task_info = (word, city_number, city_name, year, progress_manager, batch_manager, proxy_manager, cookie_manager)
                    all_tasks.append(task_info)
        
        logger.info(f"总任务数: {len(all_tasks)}")
        
        # 统计已完成的任务
        completed_tasks = sum(1 for word, city_number, city_name, year, *_ in all_tasks 
                            if progress_manager.is_completed(word, city_number, year))
        logger.info(f"已完成任务数: {completed_tasks}")
        logger.info(f"剩余任务数: {len(all_tasks) - completed_tasks}")
        
        # 并发处理任务
        success_count = 0
        failure_count = 0
        
        with ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
            # 提交所有任务
            future_to_task = {executor.submit(process_single_task, task): task for task in all_tasks}
            
            # 处理完成的任务
            for future in as_completed(future_to_task):
                task_info = future_to_task[future]
                word, city_number, city_name, year = task_info[:4]
                
                try:
                    result = future.result()
                    if result:
                        success_count += 1
                    else:
                        failure_count += 1
                        
                    # 进度显示
                    total_processed = success_count + failure_count
                    progress_pct = (total_processed / len(all_tasks)) * 100
                    logger.info(f"进度: {progress_pct:.1f}% ({total_processed}/{len(all_tasks)}), "
                              f"成功: {success_count}, 失败: {failure_count}")
                    
                except Exception as e:
                    failure_count += 1
                    logger.error(f"任务执行异常: {word} - {city_name} - {year}, 错误: {e}")
        
        # 保存最后一个批次
        batch_manager.save_final_batch()
        
        # 合并所有批次文件
        logger.info("开始合并所有批次文件...")
        if batch_manager.merge_all_batches(CONFIG['final_output']):
            logger.info(f"数据合并完成！最终文件: {CONFIG['final_output']}")
        else:
            logger.error("数据合并失败！")
        
        # 最终统计
        logger.info(f"爬取完成！成功: {success_count}, 失败: {failure_count}")
        logger.info(f"进度文件: {CONFIG['progress_file']}")
        logger.info(f"批次数据目录: {CONFIG['output_dir']}")
        logger.info(f"最终输出文件: {CONFIG['final_output']}")
        
    except KeyboardInterrupt:
        logger.info("用户中断了程序，进度已保存")
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
    finally:
        logger.info("程序结束")

if __name__ == "__main__":
    main()