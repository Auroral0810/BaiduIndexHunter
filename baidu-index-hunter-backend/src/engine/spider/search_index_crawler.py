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
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse

from src.core.logger import log
from src.utils.rate_limiter import rate_limiter
from src.utils.decorators import retry
from src.engine.crypto.cipher_generator import cipher_text_generator
from src.services.processor_service import data_processor
from src.services.storage_service import storage_service
from src.services.region_service import get_region_manager
from src.services.cookie_rotator import cookie_rotator
from src.core.config import BAIDU_INDEX_API, OUTPUT_DIR

# 自定义异常类
class NoCookieAvailableError(Exception):
    """当没有可用Cookie时抛出的异常"""
    pass

class SearchIndexCrawler:
    """百度搜索指数爬虫类（并行版本）"""
    
    def __init__(self):
        """初始化爬虫"""
        self.cookie_rotator = cookie_rotator
        self.task_id = None
        self.data_cache = []  # 全局缓存，仅用于初始化和调试
        self.stats_cache = []  # 全局缓存，仅用于初始化和调试
        self.cache_limit = 1000
        self.checkpoint_path = None
        self.output_path = None
        # 添加线程同步锁
        self.task_lock = threading.Lock()  # 保护任务状态
        self.save_lock = threading.Lock()  # 保护文件写入
        self.setup_signal_handlers()
        # 初始化任务计数器和状态变量
        self.total_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0  # 新增：追踪失败的任务数
        self.completed_keywords = set()  # 使用集合以加速查找
        self.failed_keywords = set()  # 新增：追踪失败的任务键
        self.current_keyword_index = 0
        self.current_city_index = 0
        self.current_date_range_index = 0
        self.city_dict = {}
        # 设置线程池最大工作线程数
        from src.services.config_service import config_manager
        self.max_workers = int(config_manager.get('spider.max_workers', 5))
        self.timeout = int(config_manager.get('spider.timeout', 15))
        self.retry_times = int(config_manager.get('spider.retry_times', 2))
        log.info(f"爬虫配置已加载: max_workers={self.max_workers}, timeout={self.timeout}, retry_times={self.retry_times}")
        # 修改为动态配置线程
        
    def setup_signal_handlers(self):
        """设置信号处理器以捕获中断"""
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)
        
    def handle_exit(self, signum, frame):
        """处理退出信号，保存数据和检查点"""
        log.info("接收到退出信号，正在保存数据和检查点...")
        self._flush_buffer(force=True)
        log.info(f"数据和检查点已保存。任务ID: {self.task_id}")
        sys.exit(0)
        
    def _generate_task_id(self):
        """生成唯一的任务ID"""
        return datetime.now().strftime('%Y%m%d%H%M%S')
    
    def _update_task_db_status(self, status, progress=None, error_message=None):
        """更新数据库中的任务状态、进度和错误信息 (含 WebSocket 推送)"""
        try:
            from src.data.repositories.task_repository import task_repo
            success = task_repo.update_task_progress(
                task_id=self.task_id,
                status=status,
                progress=min(float(progress or 0), 100.0) if progress is not None else None,
                completed_items=self.completed_tasks,
                failed_items=self.failed_tasks,
                error_message=error_message
            )
            
            if not success:
                log.error(f"DB Status Update Error: Task {self.task_id} not found")
                return

            try:
                from src.services.websocket_service import emit_task_update
                emit_task_update(self.task_id, {
                    'status': status, 'progress': progress or 0,
                    'completed_items': self.completed_tasks, 'failed_items': self.failed_tasks,
                    'total_items': self.total_tasks, 'error_message': error_message or ""
                })
            except: pass
        except Exception as e:
            log.error(f"DB Status Update Error: {e}")

    def _update_spider_statistics(self, data_count):
        """更新当日爬虫抓取总量统计"""
        if data_count <= 0: return
        try:
            from src.data.repositories.statistics_repository import statistics_repo
            from src.data.repositories.task_repository import task_repo
            
            task = task_repo.get_by_task_id(self.task_id)
            if not task: return
            
            # 直接调用高层方法，内部处理 Upsert 逻辑
            statistics_repo.increment_crawled_count(task.task_type, data_count)
            
        except Exception as e:
            log.error(f"Stats Update Error: {e}")

    def _flush_buffer(self, force=False):
        """将缓存数据持久化到文件并同步数据库统计"""
        with self.save_lock:
            data_to_save, stats_to_save = [], []
            with self.task_lock:
                if (force or len(self.data_cache) >= self.cache_limit) and self.data_cache:
                    data_to_save, self.data_cache = list(self.data_cache), []
                if (force or len(self.stats_cache) >= self.cache_limit) and self.stats_cache:
                    stats_to_save, self.stats_cache = list(self.stats_cache), []
            
            if not data_to_save and not stats_to_save: return
                
            try:
                if data_to_save:
                    path = os.path.join(self.output_path, f"search_index_{self.task_id}_daily_data.csv")
                    storage_service.append_to_csv(pd.DataFrame(data_to_save), path)
                    self._update_spider_statistics(len(data_to_save))
                    if not hasattr(self, '_total_saved_count'): self._total_saved_count = 0
                    self._total_saved_count += len(data_to_save)
                    progress = (self.completed_tasks / self.total_tasks * 100) if self.total_tasks > 0 else 0
                    log.info(f"进度: [{self.completed_tasks}/{self.total_tasks}] {progress:.2f}% - 持久化 {len(data_to_save)} 条记录")

                if stats_to_save:
                    path = os.path.join(self.output_path, f"search_index_{self.task_id}_stats_data.csv")
                    storage_service.append_to_csv(pd.DataFrame(stats_to_save), path)
                
                self._save_global_checkpoint()
            except Exception as e:
                log.error(f"Flush Buffer Error: {e}")
    
    def _save_global_checkpoint(self):
        """保存全局检查点（包含已完成关键词、索引等）"""
        if not hasattr(self, 'checkpoint_path') or self.checkpoint_path is None:
            log.warning("Checkpoint path is not set, skipping global checkpoint save.")
            return
            
        checkpoint_data = {
            'completed_keywords': list(self.completed_keywords), # Convert set to list for pickling
            'failed_keywords': list(self.failed_keywords), # Convert set to list for pickling
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'total_tasks': self.total_tasks,
            'city_dict': self.city_dict,
            'task_id': self.task_id,
            'output_path': self.output_path, # Save output_path
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        storage_service.save_pickle(checkpoint_data, self.checkpoint_path)
        log.info(f"检查点已保存: {self.checkpoint_path}, 已完成任务: {self.completed_tasks}/{self.total_tasks}")
    
    def _load_global_checkpoint(self, task_id):
        """加载全局检查点"""
        checkpoint_path = os.path.join(OUTPUT_DIR, f"checkpoints/search_index_checkpoint_{task_id}.pkl")
        checkpoint = storage_service.load_pickle(checkpoint_path)
        
        if checkpoint:
            self.completed_keywords = set(checkpoint.get('completed_keywords', []))
            self.failed_keywords = set(checkpoint.get('failed_keywords', []))
            self.completed_tasks = checkpoint.get('completed_tasks', 0)
            self.failed_tasks = checkpoint.get('failed_tasks', 0)
            self.total_tasks = checkpoint.get('total_tasks', 0)
            self.city_dict = checkpoint.get('city_dict', {})
            self.task_id = checkpoint.get('task_id', task_id)
            self.checkpoint_path = checkpoint_path
            self.output_path = checkpoint.get('output_path', os.path.join(OUTPUT_DIR, 'search_index', self.task_id))
            return True
        return False


    def _update_ab_sr_cookies(self):
        """更新所有账号的ab_sr cookie"""
        try:
            # log.info("开始更新所有账号的ab_sr cookie...")
            # 导入需要的模块
            from src.services.cookie_service import CookieManager
            
            # 创建Cookie管理器
            cookie_manager = CookieManager()
            
            # 更新所有账号的ab_sr cookie
            result = cookie_manager.update_ab_sr_for_all_accounts()
            
            # 关闭Cookie管理器连接
            cookie_manager.close()
            
            if 'error' in result:
                log.error(f"更新ab_sr cookie失败: {result['error']}")
                return False
            
            # log.info(f"成功更新ab_sr cookie: 更新{result['updated_count']}个，新增{result['added_count']}个，失败{result['failed_count']}个")
            
            # 更新完成后重置cookie轮换器的缓存
            self.cookie_rotator.reset_cache()
            
            return True
        except Exception as e:
            log.error(f"更新ab_sr cookie时出错: {e}")
            log.error(traceback.format_exc())
            return False
    
    @retry(max_retries=3, delay=2)
    def _get_cipher_text(self, keyword):
        """获取Cipher-Text参数"""
        encoded_keyword = keyword.replace(' ', '%20')
        cipher_url = f'{BAIDU_INDEX_API["referer"]}#/trend/{encoded_keyword}?words={encoded_keyword}'
        return cipher_text_generator.generate(cipher_url)
    
    @retry(max_retries=3, delay=2)
    def _get_search_index(self, area, keywords, start_date, end_date):
        """获取搜索指数数据"""
        # 使用rate_limiter来限制请求频率
        rate_limiter.wait()
        
        # 构建word参数
        word_list = []
        for keyword in keywords:
            word_list.append([{"name": keyword, "wordType": 1}])
        
        # 将word_list转换为JSON字符串
        word_param = json.dumps(word_list, ensure_ascii=False)
        
        # 构造参数
        params = {
            "area": area,
            "word": word_param,
            "startDate": start_date,
            "endDate": end_date
        }
        
        # 构造URL
        encoded_word = urllib.parse.quote(params["word"])
        url = f"{BAIDU_INDEX_API['search_url']}?area={params['area']}&word={encoded_word}&startDate={params['startDate']}&endDate={params['endDate']}"
        
        # 获取有效的Cookie - cookie_rotator.get_cookie()方法内部会记录使用量，不需要额外记录
        account_id, cookie_dict = self.cookie_rotator.get_cookie()
        if not cookie_dict:
            # 修改这里：不再等待，而是抛出特定异常，以便上层处理
            log.warning("所有Cookie均被锁定，无法继续爬取")
            raise NoCookieAvailableError("所有Cookie均被锁定，无法继续爬取")
            
        # 获取Cipher-Text (使用第一个关键词)
        cipher_text = self._get_cipher_text(keywords[0])
        
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
            'User-Agent': BAIDU_INDEX_API['user_agent'],
            'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
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
        """处理搜索指数数据 (单关键词)"""
        daily_list, stats_list = data_processor.process_multi_search_index_data(
            data, cookie, [keyword], city_code, city_name, start_date, end_date
        )
        return (daily_list[0] if daily_list else None), (stats_list[0] if stats_list else None)

    def _process_multi_search_index_data(self, data, cookie, keywords, city_code, city_name, start_date, end_date):
        """处理多关键词搜索指数数据"""
        return data_processor.process_multi_search_index_data(
            data, cookie, keywords, city_code, city_name, start_date, end_date
        )
    
    def _process_year_range(self, start_year, end_year):
        """处理年份范围，生成年度请求参数列表"""
        current_year = datetime.now().year
        current_month = datetime.now().month
        current_day = datetime.now().day
        
        date_ranges = []
        # 确保年份是整数类型
        try:
            start_year = int(start_year)
            end_year = int(end_year)
        except (ValueError, TypeError) as e:
            log.error(f"年份格式错误: start_year={start_year}, end_year={end_year}, 错误: {e}")
            return []

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
    
    def _process_task(self, task_data):
        """
        处理单个任务的函数，用于线程池
        
        参数:
            task_data (tuple): (keyword, city_code, city_name, start_date, end_date)
        或者 (keywords, city_code, city_name, start_date, end_date) 其中keywords是关键词列表
        
        返回值:
            对于单关键词模式: (task_key, daily_data, stats_record, is_success)
            对于批量模式: ([task_keys], daily_data_list, stats_records_list, is_success)
            其中 is_success 表示是否成功获取到有效数据
        """
        rate_limiter.wait()
        
        # 判断第一个参数是单个关键词还是关键词列表
        if isinstance(task_data[0], list):
            keywords = task_data[0]
            city_code, city_name, start_date, end_date = task_data[1:]
            is_batch = True
        else:
            keyword = task_data[0]
            keywords = [keyword]
            city_code, city_name, start_date, end_date = task_data[1:]
            is_batch = False
        
        # 检查任务是否已完成（成功完成的任务跳过，失败的任务需要重试）
        if not is_batch:
            task_key = f"{keyword}_{city_code}_{start_date}_{end_date}"
            if task_key in self.completed_keywords:
                # 如果任务已完成，直接返回None，不增加completed_tasks计数
                return None
            # 如果任务之前失败过，从失败集合中移除（准备重试）
            if task_key in self.failed_keywords:
                with self.task_lock:
                    self.failed_keywords.discard(task_key)
        else:
            # 批量模式下，检查所有关键词是否都已完成
            all_completed = True
            for keyword in keywords:
                task_key = f"{keyword}_{city_code}_{start_date}_{end_date}"
                if task_key not in self.completed_keywords:
                    all_completed = False
                    break
                # 如果任务之前失败过，从失败集合中移除（准备重试）
                if task_key in self.failed_keywords:
                    with self.task_lock:
                        self.failed_keywords.discard(task_key)
            
            if all_completed:
                return None
        
        try:
            # 获取数据
            result = self._get_search_index(city_code, keywords, start_date, end_date)
            if not result:
                log.warning(f"获取数据失败，标记为失败任务: {city_code}, {start_date}-{end_date}, 关键词数量: {len(keywords)}")
                
                # 返回失败标记，不保存空数据
                if not is_batch:
                    # 单关键词模式 - 返回失败标记
                    return task_key, None, None, False
                else:
                    # 批量模式 - 返回失败标记
                    return [f"{kw}_{city_code}_{start_date}_{end_date}" for kw in keywords], None, None, False
        except NoCookieAvailableError:
            # 向上层抛出异常，通知主线程暂停任务
            raise
        except Exception as e:
            log.error(f"处理任务时出错: {e}")
            # 返回失败标记，不保存空数据
            if not is_batch:
                # 单关键词模式 - 返回失败标记
                return task_key, None, None, False
            else:
                # 批量模式 - 返回失败标记
                return [f"{kw}_{city_code}_{start_date}_{end_date}" for kw in keywords], None, None, False
        
        data, cookie = result
        
        # 处理数据
        if not is_batch:
            # 单关键词处理
            daily_data, stats_record = self._process_search_index_data(
                data, cookie, keyword, city_code, city_name, start_date, end_date
            )
            
            # 如果处理结果为None，标记为失败
            if daily_data is None or stats_record is None:
                log.warning(f"处理数据失败，标记为失败任务: {task_key}")
                return task_key, None, None, False
            
            # 成功获取数据
            return task_key, daily_data, stats_record, True
        else:
            # 批量处理多个关键词
            daily_data_list, stats_records_list = self._process_multi_search_index_data(
                data, cookie, keywords, city_code, city_name, start_date, end_date
            )
            
            # 如果处理结果为空，标记为失败
            if not daily_data_list or not stats_records_list:
                log.warning(f"批量处理数据失败，标记为失败任务: {city_code}, {start_date}-{end_date}, 关键词数量: {len(keywords)}")
                return [f"{kw}_{city_code}_{start_date}_{end_date}" for kw in keywords], None, None, False
            
            # 成功获取数据
            return [f"{kw}_{city_code}_{start_date}_{end_date}" for kw in keywords], daily_data_list, stats_records_list, True

    
    def crawl(self, task_id=None, keywords=None, cities=None, date_ranges=None, days=None, 
              keywords_file=None, cities_file=None, date_ranges_file=None,
              year_range=None, resume=False, checkpoint_task_id=None, total_tasks=None, batch_size=5):
        """
        爬取百度搜索指数数据
        
        参数:
            task_id (str): 任务ID
            keywords (list): 关键词列表
            cities (dict): 城市代码和名称的字典 {城市代码: 城市名称}
            date_ranges (list): 日期范围列表，每个元素为 (start_date, end_date) 元组
            days (int): 预定义的天数，可以是7、30、90、180
            keywords_file (str): 关键词文件路径
            cities_file (str): 城市代码文件路径
            date_ranges_file (str): 日期范围文件路径
            year_range (tuple): 年份范围，格式为 (start_year, end_year)
            resume (bool): 是否恢复上次任务
            checkpoint_task_id (str): 要恢复的任务ID
            total_tasks (int): 总任务数（从task_executor传入）
            batch_size (int): 每批处理的关键词数量，默认为5，最大不超过5个
        """
        # 设置任务ID和检查点路径
        if resume and checkpoint_task_id:
            self.task_id = checkpoint_task_id
            loaded = self._load_global_checkpoint(checkpoint_task_id)
            if not loaded:
                log.warning(f"未找到任务ID为 {checkpoint_task_id} 的检查点，将创建新任务")
                self.task_id = self._generate_task_id()
                resume = False
            else:
                # 如果成功加载了检查点，使用检查点中的城市字典
                cities = self.city_dict
                log.info(f"从检查点恢复任务: {checkpoint_task_id}, 已完成任务数: {self.completed_tasks}")
        else:
            self.task_id = task_id if task_id else self._generate_task_id()
            # 初始化进度追踪变量
            self.completed_keywords = set()  # 改为使用set而不是list
            self.failed_keywords = set()  # 新增：追踪失败的任务
            # 重置任务计数器
            self.completed_tasks = 0
            self.failed_tasks = 0  # 新增：失败任务计数
            self.current_keyword_index = 0
            self.current_city_index = 0
            self.current_date_range_index = 0
            
        # 如果没有从检查点恢复，则需要设置输出路径和检查点路径
        if not resume:
            self.output_path = os.path.join(OUTPUT_DIR, 'search_index', self.task_id)
            os.makedirs(self.output_path, exist_ok=True)
            self.checkpoint_path = os.path.join(OUTPUT_DIR, f"checkpoints/search_index_checkpoint_{self.task_id}.pkl")
            os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)
            # 确保非恢复模式下重置完成任务计数
            self.completed_tasks = 0
            self.failed_tasks = 0  # 新增：重置失败任务计数

        # 加载关键词
        if keywords_file:
            keywords = self._load_keywords_from_file(keywords_file)
        
        if not keywords:
            log.error("未提供关键词列表")
            return False
            
        # 加载城市（如果没有从检查点恢复）
        if not resume:
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
        log.info(f"爬虫接收到的 date_ranges 参数: {date_ranges}, 类型: {type(date_ranges)}, 长度: {len(date_ranges) if date_ranges else 0}")
        
        if date_ranges_file:
            date_ranges = self._load_date_ranges_from_file(date_ranges_file)
        elif year_range:
            date_ranges = self._process_year_range(year_range[0][0], year_range[0][1])
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
        
        log.info(f"最终使用的 date_ranges 长度: {len(date_ranges)}")
        
        
        
        theoretical_total_tasks = len(keywords) * len(self.city_dict) * len(date_ranges)
        # log.info(f"理论总任务数: {theoretical_total_tasks} (关键词: {len(keywords)}, 城市: {len(self.city_dict)}, 日期范围: {len(date_ranges)})")
        # 初始设置，后面会根据实际任务列表更新
        self.total_tasks = theoretical_total_tasks
        # # 计算总任务数
        # if not resume:
        #     # 如果没有从task_executor传入总任务数，则自行计算
        #     if total_tasks is None:
        #         # 计算理论上的总任务数，但实际执行时会根据all_tasks的长度重新设置
        #         theoretical_total_tasks = len(keywords) * len(self.city_dict) * len(date_ranges)
        #         # log.info(f"理论总任务数: {theoretical_total_tasks} (关键词: {len(keywords)}, 城市: {len(self.city_dict)}, 日期范围: {len(date_ranges)})")
        #         # 初始设置，后面会根据实际任务列表更新
        #         self.total_tasks = theoretical_total_tasks
        #     else:
        #         # 如果传入了总任务数，使用传入的值
        #         self.total_tasks = total_tasks*len(date_ranges)
        #         # log.info(f"使用传入的总任务数: {self.total_tasks}")
        # else:
        #     # 如果是恢复模式且传入了总任务数，检查是否需要更新总任务数
        #     if total_tasks is not None and total_tasks > self.total_tasks:
        #         log.info(f"更新总任务数: {self.total_tasks} -> {total_tasks}")
        #         self.total_tasks = total_tasks
            
        log.info(f"任务ID: {self.task_id}")
        log.info(f"总任务数: {self.total_tasks} (关键词: {len(keywords)}, 城市: {len(self.city_dict)}, 日期范围: {len(date_ranges)})")
        
        # 上次进度更新的百分比，用于每增加5%进度时更新一次数据库
        last_progress_percent = 0
        
        # 记录上次更新ab_sr的任务数
        last_ab_sr_update_task_count = 0
        
        # 开始爬取前先更新一次ab_sr cookie
        # self._update_ab_sr_cookies()
        
        # 开始爬取
        try:
            # 准备所有任务
            all_tasks = []
            
            # 强制限制batch_size最大为5
            batch_size = min(batch_size, 5)
            log.info(f"批量处理关键词，每批次最多 {batch_size} 个关键词")
            
            # 按batch_size将关键词分组
            keyword_batches = []
            for i in range(0, len(keywords), batch_size):
                keyword_batches.append(keywords[i:i+batch_size])
            
            # 如果batch_size为1或者只有一个关键词，使用原来的方式
            if batch_size == 1 or len(keywords) == 1:
                for keyword in keywords:
                    for city_code, city_name in self.city_dict.items():
                        for start_date, end_date in date_ranges:
                            task_key = f"{keyword}_{city_code}_{start_date}_{end_date}"
                            # 检查任务是否已完成
                            if task_key in self.completed_keywords:
                                log.debug(f"跳过已完成的任务: {task_key}")
                                continue
                            all_tasks.append((keyword, city_code, city_name, start_date, end_date))
            else:
                # 批量处理模式
                for keyword_batch in keyword_batches:
                    for city_code, city_name in self.city_dict.items():
                        for start_date, end_date in date_ranges:
                            # 检查该批次中的所有关键词是否都已完成
                            all_completed = True
                            for keyword in keyword_batch:
                                task_key = f"{keyword}_{city_code}_{start_date}_{end_date}"
                                if task_key not in self.completed_keywords:
                                    all_completed = False
                                    break
                            
                            if all_completed:
                                log.debug(f"跳过已完成的批次任务: {city_code}, {start_date}-{end_date}, 关键词数量: {len(keyword_batch)}")
                                continue
                                    
                            all_tasks.append((keyword_batch, city_code, city_name, start_date, end_date))
            
            # 更新实际总任务数为需要执行的任务数量
            # self.total_tasks = len(all_tasks)
            log.info(f"准备执行 {len(all_tasks)} 个任务，使用 {self.max_workers} 个线程")
            
            # 如果所有任务都已完成
            if not all_tasks:
                log.info("所有任务都已完成，无需执行")
                self._update_task_db_status('completed', progress=100)
                return True
            
            # 使用线程池执行任务
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_task = {executor.submit(self._process_task, task): task for task in all_tasks}
                
                for future in as_completed(future_to_task):
                    try:
                        result = future.result()
                        if not result: continue
                        
                        is_batch = isinstance(result[0], list)
                        task_keys, daily_data, stats_records, is_success = result # 此时应统一为4个返回值
                        
                        with self.task_lock:
                            if is_success:
                                keys = task_keys if is_batch else [task_keys]
                                self.completed_keywords.update(keys)
                                self.completed_tasks += len(keys)
                                if daily_data: self.data_cache.extend(daily_data)
                                if stats_records:
                                    if isinstance(stats_records, list): self.stats_cache.extend(stats_records)
                                    else: self.stats_cache.append(stats_records)
                            else:
                                keys = task_keys if is_batch else [task_keys]
                                self.failed_keywords.update(keys)
                                self.failed_tasks += len(keys)
                            
                            if self.completed_tasks % 20 == 0: self._save_global_checkpoint()

                        if len(self.data_cache) >= 200:
                            self._flush_buffer()
                            prog = (self.completed_tasks + self.failed_tasks) / self.total_tasks * 100
                            self._update_task_db_status('running', progress=prog)

                    except NoCookieAvailableError:
                        log.error("Cookie 耗尽，暂停任务")
                        self._flush_buffer(force=True)
                        self._update_task_db_status('paused', error_message="所有 Cookie 均被锁定，等待自动恢复")
                        for f in future_to_task: f.cancel()
                        return False
                    except Exception as e:
                        log.error(f"子任务异常: {e}")

            self._flush_buffer(force=True)
            status = 'completed' if self.failed_tasks == 0 else 'failed'
            msg = f"完成但有 {self.failed_tasks} 项失败" if status == 'failed' else None
            self._update_task_db_status(status, progress=100, error_message=msg)
            return status == 'completed'

        except Exception as e:
            log.error(f"爬取主流程失败: {e}")
            self._flush_buffer(force=True)
            self._update_task_db_status('failed', error_message=str(e))
            return False
    
    def resume_task(self, task_id):
        """恢复指定的任务"""
        log.info(f"尝试恢复任务: {task_id}")
        
        # 检查检查点文件是否存在
        checkpoint_path = os.path.join(OUTPUT_DIR, f"checkpoints/search_index_checkpoint_{task_id}.pkl")
        if not os.path.exists(checkpoint_path):
            log.warning(f"未找到任务 {task_id} 的检查点文件，无法恢复")
            return False
            
        # 检查任务在数据库中的状态
        try:
            from src.data.repositories.mysql_manager import MySQLManager
            mysql = MySQLManager()
            
            # 查询任务信息
            query = """
                SELECT status, progress, completed_items, error_message 
                FROM spider_tasks 
                WHERE task_id = %s
            """
            task_info = mysql.fetch_one(query, (task_id,))
            
            if not task_info:
                log.warning(f"数据库中未找到任务 {task_id} 的信息，无法恢复")
                return False
                
            log.info(f"任务 {task_id} 当前状态: {task_info['status']}, 进度: {task_info['progress']}%, 已完成项: {task_info['completed_items']}")
            
            # 更新任务状态为进行中
            update_query = """
                UPDATE spider_tasks 
                SET status = 'running', error_message = %s, update_time = %s
                WHERE task_id = %s
            """
            mysql.execute_query(
                update_query, 
                (f"任务于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 恢复执行", datetime.now(), task_id)
            )
            
            log.info(f"已将任务 {task_id} 状态更新为进行中")
            
        except Exception as e:
            log.error(f"查询或更新任务状态失败: {e}")
            log.error(traceback.format_exc())
        
        # 恢复任务执行
        return self.crawl(resume=True, checkpoint_task_id=task_id)
    
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

 