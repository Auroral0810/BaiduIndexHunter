"""
搜索指数爬虫（日度、周度数据和整体统计数据）
"""
import pandas as pd
import requests
import json
import time
import signal
import os
import sys
import threading
import pickle
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.logger import log
from utils.rate_limiter import rate_limiter
from utils.retry_decorator import retry
from utils.cipher_text import cipher_text_generator
from utils.data_processor import data_processor
from cookie_manager.cookie_rotator import cookie_rotator
from config.settings import BAIDU_INDEX_API, OUTPUT_DIR

class SearchIndexCrawler:
    """百度搜索指数爬虫类"""
    
    def __init__(self):
        """初始化爬虫"""
        self.cookie_rotator = cookie_rotator
        self.task_id = None
        self.data_cache = []
        self.stats_cache = []
        self.cache_limit = 100
        self.checkpoint_path = None
        self.output_path = None
        self.lock = threading.Lock()
        self.setup_signal_handlers()
        self.total_tasks = 0
        self.completed_tasks = 0
        self.city_dict = {}  # 城市代码到名称的映射
        
    def setup_signal_handlers(self):
        """设置信号处理器以捕获中断"""
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)
        
    def handle_exit(self, signum, frame):
        """处理退出信号，保存数据和检查点"""
        log.info("接收到退出信号，正在保存数据和检查点...")
        self._save_data_cache(force=True)
        self._save_global_checkpoint()
        log.info(f"数据和检查点已保存。任务ID: {self.task_id}")
        sys.exit(0)
        
    def _generate_task_id(self):
        """生成唯一的任务ID"""
        return datetime.now().strftime('%Y%m%d%H%M%S')
        
    def _save_data_cache(self, force=False):
        """保存数据缓存到CSV文件"""
        with self.lock:
            if (len(self.data_cache) >= self.cache_limit or force) and self.data_cache:
                # 保存日度/周度数据
                daily_df = pd.DataFrame(self.data_cache)
                daily_path = os.path.join(self.output_path, f"{self.task_id}_daily_data.csv")
                
                # 判断文件是否存在，决定是否写入表头
                file_exists = os.path.isfile(daily_path)
                daily_df.to_csv(daily_path, mode='a', header=not file_exists, index=False, encoding='utf-8-sig')
                
                # 清空缓存
                self.data_cache = []
                log.info(f"已保存{len(daily_df)}条数据记录到 {daily_path}")
                
            if (len(self.stats_cache) >= self.cache_limit or force) and self.stats_cache:
                # 保存统计数据
                stats_df = pd.DataFrame(self.stats_cache)
                stats_path = os.path.join(self.output_path, f"{self.task_id}_stats_data.csv")
                
                # 判断文件是否存在，决定是否写入表头
                file_exists = os.path.isfile(stats_path)
                stats_df.to_csv(stats_path, mode='a', header=not file_exists, index=False, encoding='utf-8-sig')
                
                # 清空缓存
                self.stats_cache = []
                log.info(f"已保存{len(stats_df)}条统计数据记录到 {stats_path}")
    
    def _save_global_checkpoint(self):
        """保存全局检查点"""
        checkpoint = {
            'task_id': self.task_id,
            'completed_tasks': self.completed_tasks,
            'total_tasks': self.total_tasks
        }
        
        with open(self.checkpoint_path, 'wb') as f:
            pickle.dump(checkpoint, f)
        log.info(f"检查点已保存: {self.checkpoint_path}")
        
    def _load_global_checkpoint(self, task_id):
        """加载全局检查点"""
        self.task_id = task_id
        self.checkpoint_path = os.path.join(OUTPUT_DIR, f"checkpoints/{self.task_id}_checkpoint.pkl")
        
        # 确保检查点目录存在
        os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)
        
        if os.path.exists(self.checkpoint_path):
            with open(self.checkpoint_path, 'rb') as f:
                checkpoint = pickle.load(f)
                self.completed_tasks = checkpoint.get('completed_tasks', 0)
                self.total_tasks = checkpoint.get('total_tasks', 0)
            log.info(f"已加载检查点: {self.checkpoint_path}, 已完成任务: {self.completed_tasks}/{self.total_tasks}")
            return True
        return False
    
    def _decrypt(self, key, data):
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
    
    @retry(max_retries=3, delay=2)
    def _get_cipher_text(self, keyword):
        """获取Cipher-Text参数"""
        encoded_keyword = keyword.replace(' ', '%20')
        cipher_url = f'{BAIDU_INDEX_API["referer"]}#/trend/{encoded_keyword}?words={encoded_keyword}'
        return cipher_text_generator.generate(cipher_url)
    
    @retry(max_retries=3, delay=2)
    def _get_key(self, uniqid, cookie):
        """获取解密密钥"""
        params = {'uniqid': uniqid}
        
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': BAIDU_INDEX_API['referer'],
            'User-Agent': BAIDU_INDEX_API['user_agent'],
        }
        
        response = requests.get(
            'https://index.baidu.com/Interface/ptbk', 
            params=params, 
            cookies=cookie, 
            headers=headers
        )
        
        if response.status_code != 200:
            log.error(f"获取解密密钥失败: {response.status_code}")
            return None
            
        data = response.json()
        if data.get('status') != 0:
            log.error(f"获取解密密钥失败: {data}")
            return None
            
        return data.get('data')
    
    @retry(max_retries=3, delay=2)
    def _get_search_index(self, area, keywords, start_date, end_date):
        """获取搜索指数数据"""
        # 使用rate_limiter来限制请求频率
        rate_limiter.wait()
        
        # 构建word参数
        word_param = []
        for keyword in keywords:
            word_param.append({"name": keyword, "wordType": 1})
        
        # 构建请求URL
        encoded_word_param = json.dumps([word_param])
        url = f"{BAIDU_INDEX_API['search_url']}?area={area}&word={encoded_word_param}&startDate={start_date}&endDate={end_date}"
        
        # 获取有效的Cookie
        account_id, cookie_dict = self.cookie_rotator.get_cookie()
        if not cookie_dict:
            log.warning("所有Cookie均被锁定，等待30分钟后重试")
            time.sleep(1800)  # 等待30分钟
            return None
            
        # 获取Cipher-Text
        cipher_text = self._get_cipher_text(keywords[0])
        
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Cipher-Text': cipher_text,
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': BAIDU_INDEX_API['referer'],
            'User-Agent': BAIDU_INDEX_API['user_agent'],
        }
        
        response = requests.get(url, cookies=cookie_dict, headers=headers)
        
        if response.status_code != 200:
            log.error(f"请求失败: {response.status_code}")
            return None
            
        data = response.json()
        
        # 检查响应状态
        status = data.get('status')
        if status == 10001:  # 请求被锁定
            log.warning(f"Cookie被临时锁定: {account_id}")
            self.cookie_rotator.report_cookie_status(account_id, False)
            return None
        elif status == 10000:  # 未登录
            log.warning(f"Cookie无效或已过期: {account_id}")
            self.cookie_rotator.report_cookie_status(account_id, False, permanent=True)
            return None
        elif status != 0:
            log.error(f"请求失败: {data}")
            return None
            
        return data, cookie_dict
    
    def _process_search_index_data(self, data, cookie, keyword, city_code, city_name, start_date, end_date):
        """处理搜索指数数据"""
        if not data or not data.get('data') or not data['data'].get('userIndexes'):
            log.warning(f"数据为空或格式不正确: {data}")
            return None, None
            
        try:
            user_indexes = data['data']['userIndexes'][0]
            uniqid = data['data']['uniqid']
            
            # 获取解密密钥
            key = self._get_key(uniqid, cookie)
            if not key:
                log.error("获取解密密钥失败")
                return None, None
                
            # 获取各终端数据
            all_data = user_indexes['all']['data']
            wise_data = user_indexes['wise']['data']
            pc_data = user_indexes['pc']['data']
            
            # 解密数据
            decrypted_all = self._decrypt(key, all_data)
            decrypted_wise = self._decrypt(key, wise_data)
            decrypted_pc = self._decrypt(key, pc_data)
            
            # 调用data_processor处理数据
            return data_processor.process_search_index_daily_data(
                data, cookie, keyword, city_code, city_name, 
                start_date, end_date, decrypted_all, decrypted_wise, decrypted_pc
            )
            
        except Exception as e:
            log.error(f"处理数据时出错: {str(e)}")
            return None, None
    
    def _process_year_range(self, start_year, end_year):
        """处理年份范围，生成年度请求参数列表"""
        current_year = datetime.now().year
        current_month = datetime.now().month
        current_day = datetime.now().day
        
        date_ranges = []
        
        for year in range(start_year, end_year + 1):
            if year < current_year:
                # 完整年份
                start_date = f"{year}-01-01"
                end_date = f"{year}-12-31"
            else:
                # 当年截止到今天
                start_date = f"{year}-01-01"
                end_date = datetime.now().strftime('%Y-%m-%d')
                
            date_ranges.append((start_date, end_date))
            
        return date_ranges
    
    def _load_keywords_from_file(self, file_path):
        """从文件加载关键词列表"""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.xlsx':
            df = pd.read_excel(file_path)
            # 假设关键词在第一列
            return df.iloc[:, 0].tolist()
        elif ext == '.csv':
            df = pd.read_csv(file_path)
            # 假设关键词在第一列
            return df.iloc[:, 0].tolist()
        elif ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        else:
            log.error(f"不支持的文件格式: {ext}")
            return []
    
    def _load_cities_from_file(self, file_path):
        """从文件加载城市代码列表"""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.xlsx':
            df = pd.read_excel(file_path)
            # 假设城市代码和城市名在前两列
            return dict(zip(df.iloc[:, 0].astype(int).tolist(), df.iloc[:, 1].tolist()))
        elif ext == '.csv':
            df = pd.read_csv(file_path)
            # 假设城市代码和城市名在前两列
            return dict(zip(df.iloc[:, 0].astype(int).tolist(), df.iloc[:, 1].tolist()))
        else:
            log.error(f"不支持的文件格式: {ext}")
            return {}
    
    def _load_date_ranges_from_file(self, file_path):
        """从文件加载日期范围列表"""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.xlsx':
            df = pd.read_excel(file_path)
            # 假设起始日期和结束日期在名为'start_date'和'end_date'的列
            return list(zip(df['start_date'].tolist(), df['end_date'].tolist()))
        elif ext == '.csv':
            df = pd.read_csv(file_path)
            # 假设起始日期和结束日期在名为'start_date'和'end_date'的列
            return list(zip(df['start_date'].tolist(), df['end_date'].tolist()))
        elif ext == '.txt':
            date_ranges = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) == 2:
                        date_ranges.append((parts[0], parts[1]))
            return date_ranges
        else:
            log.error(f"不支持的文件格式: {ext}")
            return []
    
    def crawl(self, keywords=None, cities=None, date_ranges=None, days=None, 
              keywords_file=None, cities_file=None, date_ranges_file=None,
              year_range=None, resume=False, task_id=None):
        """
        爬取百度搜索指数数据
        
        参数:
            keywords (list): 关键词列表
            cities (dict): 城市代码和名称的字典 {城市代码: 城市名称}
            date_ranges (list): 日期范围列表，每个元素为 (start_date, end_date) 元组
            days (int): 预定义的天数，可以是7、30、90、180
            keywords_file (str): 关键词文件路径
            cities_file (str): 城市代码文件路径
            date_ranges_file (str): 日期范围文件路径
            year_range (tuple): 年份范围，格式为 (start_year, end_year)
            resume (bool): 是否恢复上次任务
            task_id (str): 要恢复的任务ID
        """
        # 加载关键词
        if keywords_file:
            keywords = self._load_keywords_from_file(keywords_file)
        
        if not keywords:
            log.error("未提供关键词列表")
            return False
            
        # 加载城市
        if cities_file:
            self.city_dict = self._load_cities_from_file(cities_file)
            cities = self.city_dict
        elif cities:
            # 处理前端传来的城市参数格式
            if isinstance(cities, dict):
                processed_cities = {}
                for code, city_info in cities.items():
                    if isinstance(city_info, dict) and 'name' in city_info and 'code' in city_info:
                        processed_cities[city_info['code']] = city_info['name']
                    else:
                        processed_cities[code] = str(city_info)
                self.city_dict = processed_cities
            else:
                self.city_dict = cities
        else:
            # 默认使用全国
            cities = {0: "全国"}
            self.city_dict = cities
            
        # 处理日期范围
        if date_ranges_file:
            date_ranges = self._load_date_ranges_from_file(date_ranges_file)
        elif year_range:
            date_ranges = self._process_year_range(year_range[0], year_range[1])
        elif days:
            # 使用预定义的天数
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days-1)).strftime('%Y-%m-%d')
            date_ranges = [(start_date, end_date)]
        elif not date_ranges:
            # 默认使用最近30天
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=29)).strftime('%Y-%m-%d')
            date_ranges = [(start_date, end_date)]
            
        # 设置任务ID和输出路径
        if resume and task_id:
            self.task_id = task_id
            loaded = self._load_global_checkpoint(task_id)
            if not loaded:
                log.warning(f"未找到任务ID为 {task_id} 的检查点，将创建新任务")
                self.task_id = self._generate_task_id()
        else:
            self.task_id = self._generate_task_id()
            
        # 设置输出路径和检查点路径
        self.output_path = os.path.join(OUTPUT_DIR, 'search_index', self.task_id)
        os.makedirs(self.output_path, exist_ok=True)
        self.checkpoint_path = os.path.join(OUTPUT_DIR, f"checkpoints/{self.task_id}_checkpoint.pkl")
        os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)
        
        # 计算总任务数
        self.total_tasks = len(keywords) * len(self.city_dict) * len(date_ranges)
        log.info(f"任务ID: {self.task_id}")
        log.info(f"总任务数: {self.total_tasks} (关键词: {len(keywords)}, 城市: {len(self.city_dict)}, 日期范围: {len(date_ranges)})")
        
        # 开始爬取
        try:
            for keyword in keywords:
                for city_code, city_name in self.city_dict.items():
                    for start_date, end_date in date_ranges:
                        # 检查是否已完成该任务
                        current_task = self.completed_tasks + 1
                        if current_task <= self.completed_tasks and resume:
                            continue
                            
                        log.info(f"正在处理 [{current_task}/{self.total_tasks}] - 关键词: {keyword}, 城市: {city_name}, 日期: {start_date} 至 {end_date}")
                        
                        # 获取数据
                        result = self._get_search_index(city_code, [keyword], start_date, end_date)
                        if not result:
                            log.warning(f"获取数据失败，跳过当前任务")
                            continue
                            
                        data, cookie = result
                        
                        # 处理数据
                        daily_data, stats_record = self._process_search_index_data(
                            data, cookie, keyword, city_code, city_name, start_date, end_date
                        )
                        
                        if daily_data:
                            # 添加到缓存
                            self.data_cache.extend(daily_data)
                            self.stats_cache.append(stats_record)
                            
                            # 更新完成任务数
                            self.completed_tasks += 1
                            
                            # 保存检查点
                            self._save_global_checkpoint()
                            
                            # 定期保存数据
                            self._save_data_cache()
                        else:
                            log.warning(f"处理数据失败，跳过当前任务")
                            
            # 最后保存所有剩余数据
            self._save_data_cache(force=True)
            log.info(f"任务完成! 总共处理了 {self.completed_tasks}/{self.total_tasks} 个任务")
            return True
            
        except Exception as e:
            log.error(f"爬取过程中出错: {str(e)}")
            # 保存当前进度和数据
            self._save_data_cache(force=True)
            self._save_global_checkpoint()
            return False
    
    def resume_task(self, task_id):
        """恢复指定的任务"""
        return self.crawl(resume=True, task_id=task_id)
    
    def list_tasks(self):
        """列出所有任务及其状态"""
        checkpoint_dir = os.path.join(OUTPUT_DIR, "checkpoints")
        if not os.path.exists(checkpoint_dir):
            log.info("没有找到任何任务")
            return []
            
        tasks = []
        for file in os.listdir(checkpoint_dir):
            if file.endswith("_checkpoint.pkl"):
                task_id = file.split("_checkpoint.pkl")[0]
                checkpoint_path = os.path.join(checkpoint_dir, file)
                
                with open(checkpoint_path, 'rb') as f:
                    checkpoint = pickle.load(f)
                    completed = checkpoint.get('completed_tasks', 0)
                    total = checkpoint.get('total_tasks', 0)
                    
                tasks.append({
                    'task_id': task_id,
                    'completed': completed,
                    'total': total,
                    'progress': f"{completed}/{total} ({completed/total*100:.2f}%)" if total > 0 else "0%"
                })
                
        return tasks

# 创建爬虫实例
search_index_crawler = SearchIndexCrawler()

 