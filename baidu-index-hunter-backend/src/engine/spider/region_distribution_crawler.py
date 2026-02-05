"""
地域分布爬虫（人群画像的地域分布）
"""
import pandas as pd
import requests
import json
import time
import os
import pickle
import signal
import atexit
from datetime import datetime, timedelta
import threading
import sys
import os
import json
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目根目录到Python路径
from src.core.logger import log
from src.utils.rate_limiter import rate_limiter
from src.utils.decorators import retry
from src.engine.crypto.cipher_generator import cipher_text_generator
from src.services.cookie_rotator import cookie_rotator
from src.core.config import BAIDU_INDEX_API, OUTPUT_DIR
from src.services.processor_service import data_processor
from fake_useragent import UserAgent


class RegionDistributionCrawler:
    """地域分布爬虫，负责获取百度指数的地域分布数据"""
    
    # 预定义的天数选项
    DAYS_OPTIONS = [7, 30, 90, 180, 365]
    
    def __init__(self):
        """初始化地域分布爬虫"""
        self.region_api_url = BAIDU_INDEX_API['region_api_url']
        self.referer = BAIDU_INDEX_API['referer']
        self.ua = UserAgent()
        self.checkpoint_dir = os.path.join(OUTPUT_DIR, 'checkpoints')
        self.output_dir = os.path.join(OUTPUT_DIR, 'region_distributions')
        
        # 创建必要的目录
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 初始化任务状态
        self.task_status = {}
        self.lock = threading.RLock()
        self.save_lock = threading.Lock()  # 保护文件写入
        
        # 初始化数据缓存
        self.data_cache = []
        self.data_cache_size = 100  # 每收集100条数据就保存一次
        
        # 初始化任务计数器和状态变量
        self.total_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0  # 新增：追踪失败的任务数
        self.completed_task_keys = set()  # 使用集合以加速查找
        self.failed_task_keys = set()  # 新增：追踪失败的任务键
        self.task_id = None
        self.output_path = None  # 输出路径，在crawl方法中设置
        self._shutdown_flag = False  # 退出标志
        
        # 设置线程池最大工作线程数
        try:
            from src.services.config_service import config_manager
            self.max_workers = int(config_manager.get('spider.max_workers', 20))
            self.timeout = int(config_manager.get('spider.timeout', 15))
            self.retry_times = int(config_manager.get('spider.retry_times', 2))
        except:
            # 如果无法加载配置，使用默认值
            self.max_workers = 20
            self.timeout = 15
            self.retry_times = 2
        log.info(f"爬虫配置已加载: max_workers={self.max_workers}, timeout={self.timeout}, retry_times={self.retry_times}")
        
        # 注册退出处理函数
        atexit.register(self._save_on_exit)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """
        处理程序中断信号
        :param sig: 信号类型
        :param frame: 当前帧
        """
        log.info(f"接收到中断信号 {sig}，正在保存数据和检查点...")
        try:
            # 设置退出标志，让线程池知道要退出
            self._shutdown_flag = True
            # 保存数据和检查点
            self._save_on_exit()
        except Exception as e:
            log.error(f"信号处理时出错: {e}")
        finally:
            # 强制退出
            import os
            os._exit(0)
    
    def _save_on_exit(self):
        """在程序退出时保存数据和检查点"""
        log.info("程序即将退出，保存数据和检查点...")
        try:
            # 使用超时机制避免死锁
            import threading
            save_completed = threading.Event()
            
            def save_data():
                try:
                    # 保存数据缓存（不使用锁，因为可能已经被持有）
                    self._save_data_cache_internal(force=True)
                    # 保存当前任务状态作为检查点
                    if self.task_id:
                        self._save_global_checkpoint(self.task_id)
                    save_completed.set()
                except Exception as e:
                    log.error(f"保存数据时出错: {e}")
                    save_completed.set()
            
            # 在单独的线程中执行保存操作
            save_thread = threading.Thread(target=save_data, daemon=True)
            save_thread.start()
            
            # 等待最多2秒
            if not save_completed.wait(timeout=2):
                log.warning("保存数据超时，强制退出")
        except Exception as e:
            log.error(f"退出处理时出错: {e}")
    
    def _save_data_cache(self, force=False, status=None):
        """
        保存数据缓存到CSV文件（带锁保护）
        :param force: 是否强制保存，即使缓存未达到阈值
        :param status: 任务状态，如果是"completed"则更新统计数据
        :return: 是否保存成功
        """
        with self.save_lock:
            return self._save_data_cache_internal(force=force, status=status)
    
    def _save_data_cache_internal(self, force=False, status=None):
        """
        保存数据缓存到CSV文件（内部实现，不获取锁）
        :param force: 是否强制保存，即使缓存未达到阈值
        :param status: 任务状态，如果是"completed"则更新统计数据
        :return: 是否保存成功
        """
        # 如果缓存为空，不保存
        if not self.data_cache:
            return False
        
        # 如果缓存未达到阈值且非强制保存，不保存
        if len(self.data_cache) < self.data_cache_size and not force:
            return False
        
        # 获取当前任务ID
        task_id = self.task_id
        if not task_id:
            log.warning("无法获取当前任务ID，使用时间戳作为文件名")
            task_id = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # 创建DataFrame
        df = pd.DataFrame(self.data_cache)
        
        # 记录实际保存的数据条数
        data_count = len(df)
        
        # 构建输出文件路径
        if self.output_path:
            output_path = os.path.join(self.output_path, f"region_distributions_{task_id}.csv")
        else:
            output_path = os.path.join(self.output_dir, task_id, f"region_distributions_{task_id}.csv")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 保存数据
        try:
            if os.path.exists(output_path):
                # 追加到现有文件
                data_processor.append_to_csv(df, output_path)
            else:
                # 创建新文件
                data_processor.save_to_csv(df, output_path)
            
            log.info(f"成功保存 {data_count} 条数据到 {output_path}")
            
            # 更新任务状态中的输出文件路径
            if task_id in self.task_status:
                self.task_status[task_id]['output_file'] = output_path
            elif self.task_id == task_id:
                # 如果task_status中没有该任务，创建一个基本记录
                if task_id not in self.task_status:
                    self.task_status[task_id] = {}
                self.task_status[task_id]['output_file'] = output_path
            
            # 清空缓存
            self.data_cache = []
            
            # 如果是任务完成时的保存，更新统计数据
            if status == "completed":
                try:
                    # 计算该任务的总爬取数据条数
                    total_crawled = 0
                    
                    # 计算文件的行数
                    if os.path.exists(output_path):
                        with open(output_path, 'r', encoding='utf-8-sig') as f:
                            total_crawled += sum(1 for _ in f) - 1  # 减去表头行
                    
                    # 获取当前日期
                    stat_date = datetime.now().date()
                    
                    # 连接数据库
                    from src.data.repositories.mysql_manager import MySQLManager
                    mysql = MySQLManager()
                    
                    # 查询当前任务信息
                    task_query = """
                        SELECT task_type FROM spider_tasks WHERE task_id = %s
                    """
                    task = mysql.fetch_one(task_query, (task_id,))
                    
                    if not task:
                        log.warning(f"更新统计数据失败：任务 {task_id} 不存在")
                        return True
                    
                    task_type = task['task_type']
                    
                    # 检查该日期是否已有统计记录
                    check_query = """
                        SELECT id, total_crawled_items FROM spider_statistics 
                        WHERE stat_date = %s AND task_type = %s
                    """
                    stats = mysql.fetch_one(check_query, (stat_date, task_type))
                    
                    if stats:
                        # 当前累计爬取数据条数
                        current_total_crawled = stats.get('total_crawled_items', 0) or 0
                        # 更新后的累计爬取数据条数
                        new_total_crawled = current_total_crawled + total_crawled
                        
                        # 更新统计记录
                        update_query = """
                            UPDATE spider_statistics
                            SET total_crawled_items = %s,
                                update_time = %s
                            WHERE id = %s
                        """
                        mysql.execute_query(update_query, (new_total_crawled, datetime.now(), stats['id']))
                        
                        log.info(f"更新累计爬取数据条数: {current_total_crawled} -> {new_total_crawled} (新增: {total_crawled})")
                    else:
                        # 未找到当日统计记录，创建一条新记录
                        insert_query = """
                            INSERT INTO spider_statistics 
                            (stat_date, task_type, total_tasks, completed_tasks, failed_tasks, total_crawled_items, update_time) 
                            VALUES (%s, %s, 1, 1, 0, %s, %s)
                        """
                        now = datetime.now()
                        mysql.execute_query(insert_query, (stat_date, task_type, total_crawled, now))
                        
                        log.info(f"创建新的统计记录，初始累计爬取数据条数: {total_crawled}")
                
                except Exception as e:
                    log.error(f"在_save_data_cache中更新统计数据失败: {e}")
                    log.error(traceback.format_exc())
            
            return True
        except Exception as e:
            log.error(f"保存数据缓存失败: {e}")
            return False
    
    def _get_checkpoint_path(self, task_id):
        """
        获取全局检查点文件路径
        :param task_id: 任务ID
        :return: 检查点文件路径
        """
        return os.path.join(self.checkpoint_dir, f"region_distributions_checkpoint_{task_id}.pkl")
    
    def _save_global_checkpoint(self, task_id=None):
        """
        保存全局检查点
        :param task_id: 任务ID，如果为None则使用self.task_id
        """
        if task_id is None:
            task_id = self.task_id
        if not task_id:
            log.warning("无法保存检查点：任务ID为空")
            return
        
        checkpoint_path = self._get_checkpoint_path(task_id)
        try:
            with self.lock:
                checkpoint_data = {
                    'task_id': task_id,
                    'completed_tasks': self.completed_tasks,
                    'total_tasks': self.total_tasks,
                    'completed_task_keys': list(self.completed_task_keys),
                    'save_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                # 如果task_status中有该任务的状态，合并进去
                if task_id in self.task_status:
                    checkpoint_data.update(self.task_status[task_id])
                
                with open(checkpoint_path, 'wb') as f:
                    pickle.dump(checkpoint_data, f)
            log.debug(f"已保存全局检查点: {checkpoint_path}")
        except Exception as e:
            log.error(f"保存全局检查点失败: {e}")
    
    def _load_global_checkpoint(self, task_id):
        """
        加载全局检查点
        :param task_id: 任务ID
        :return: 任务状态，如果不存在则返回None
        """
        checkpoint_path = self._get_checkpoint_path(task_id)
        if not os.path.exists(checkpoint_path):
            return None
        
        try:
            with open(checkpoint_path, 'rb') as f:
                status = pickle.load(f)
            log.info(f"已加载全局检查点: {checkpoint_path}")
            return status
        except Exception as e:
            log.error(f"加载全局检查点失败: {e}")
            return None
    
    def _get_output_path(self, task_id, file_type='csv'):
        """
        获取输出文件路径
        :param task_id: 任务ID
        :param file_type: 文件类型，默认为csv
        :return: 输出文件路径
        """
        # 创建任务目录
        task_dir = os.path.join(self.output_dir, task_id)
        os.makedirs(task_dir, exist_ok=True)
        return os.path.join(task_dir, f"region_distributions_{task_id}.{file_type}")
    
    def _get_current_task_id(self):
        """
        获取当前正在执行的任务ID
        :return: 任务ID，如果没有当前任务则返回None
        """
        return self.task_id
    
    def _calculate_date_range(self, days=None, start_date=None, end_date=None):
        """
        计算日期范围
        :param days: 天数，可选值：7, 30, 90, 180, 365
        :param start_date: 开始日期，格式：YYYY-MM-DD
        :param end_date: 结束日期，格式：YYYY-MM-DD
        :return: (start_date, end_date, days)
        """
        # 如果指定了开始和结束日期，则使用自定义日期范围
        if start_date and end_date:
            return start_date, end_date, None
        
        # 如果指定了天数，则计算开始日期
        if days in self.DAYS_OPTIONS:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            return start_date, end_date, days
        
        # 默认使用30天
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        return start_date, end_date, 30
    
    @retry(max_retries=2)
    def get_region_distribution(self, keywords, region=0, days=None, start_date=None, end_date=None):
        """
        获取地域分布数据
        :param keywords: 关键词列表（最多5个）或字符串（逗号分隔）
        :param region: 地区代码，0表示全国
        :param days: 天数，可选值：7, 30, 90, 180, 365（如果提供了start_date和end_date，此参数会被忽略）
        :param start_date: 开始日期，格式：YYYY-MM-DD
        :param end_date: 结束日期，格式：YYYY-MM-DD
        :return: 地域分布数据字典或None（请求失败）
        """
        try:
            # 确保关键词是列表格式
            if isinstance(keywords, str):
                keywords = [kw.strip() for kw in keywords.split(',') if kw.strip()]
            elif isinstance(keywords, list):
                keywords = [kw for kw in keywords if kw]
            else:
                log.error(f"无效的关键词格式: {type(keywords)}")
                return None
            
            # 限制最多5个关键词
            if len(keywords) > 5:
                log.warning(f"关键词数量超过5个，只使用前5个: {keywords[:5]}")
                keywords = keywords[:5]
            
            # 将关键词列表转换为逗号分隔的字符串
            keywords_str = ','.join(keywords)
            
            # 如果提供了start_date和end_date，使用它们；否则计算日期范围
            if start_date and end_date:
                days_param = None
            else:
                start_date, end_date, days_param = self._calculate_date_range(days, start_date, end_date)
            
            # 获取一个可用的cookie
            account_id, cookie_dict = cookie_rotator.get_cookie()
            if not cookie_dict:
                log.warning(f"无法获取可用Cookie进行请求 {keywords}，所有Cookie可能都被锁定")
                # 等待有可用的cookie (最多等待30秒)
                if cookie_rotator.wait_for_available_cookie(timeout=30):
                    log.info(f"检测到有可用Cookie，重试获取 {keywords}")
                    # 重新尝试获取cookie
                    account_id, cookie_dict = cookie_rotator.get_cookie()
                    if not cookie_dict:
                        log.error(f"尽管收到可用Cookie通知，但仍无法获取Cookie，放弃请求 {keywords}")
                        return None
                else:
                    log.error(f"等待可用Cookie超时，放弃请求 {keywords}")
                    return None
            
            # 构建请求URL参数（按照指定格式：region, word, startDate, endDate, days）
            # days 参数始终存在，如果未指定则为空字符串
            days_str = str(days_param) if days_param else ""
            url_params = {
                'region': str(region),
                'word': keywords_str,  # 使用逗号分隔的关键词字符串
                'startDate': start_date,
                'endDate': end_date,
                'days': days_str
            }
            
            # 构建URL查询字符串
            import urllib.parse
            query_string = urllib.parse.urlencode(url_params)
            url = f'{self.region_api_url}?{query_string}'
            
            log.debug(f"请求URL参数: {url_params}")
            
            # 构建请求头
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Pragma': 'no-cache',
                'Referer': self.referer,
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': self.ua.random,
                'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
            }
            
            # 频率控制
            rate_limiter.wait()
            
            # 发送请求
            region_name = "全国" if region == 0 else f"地区ID: {region}"
            log.info(f"请求地域分布: {keywords_str} ({len(keywords)}个关键词), {region_name}, 日期范围: {start_date} 至 {end_date}")
            response = requests.get(
                url=url,
                headers=headers,
                cookies=cookie_dict,
                timeout=10
            )
            
            # 检查响应状态
            if response.status_code != 200:
                log.error(f"请求失败，状态码: {response.status_code}, 响应内容: {response.text}")
                cookie_rotator.report_cookie_status(account_id, False)
                return None
            
            # 解析响应内容
            result = response.json()
            
            # 检查API返回的状态码
            if result.get('status') != 0:
                error_msg = result.get('message', '未知错误')
                log.error(f"API返回错误: {error_msg}")
                
                # 如果是"not login"错误，将cookie标记为永久封禁
                if error_msg == "not login":
                    log.error(f"检测到'not login'错误，账号 {account_id} 的Cookie已失效，将被永久封禁")
                    cookie_rotator.report_cookie_status(account_id, False, permanent=True)
                    
                    # 等待看是否有其他可用Cookie
                    if cookie_rotator.wait_for_available_cookie(timeout=10):
                        log.info(f"检测到有其他可用Cookie，重试获取 {keywords}")
                        # 递归调用自身重试
                        return self.get_region_distribution(keywords, region, days, start_date, end_date)
                else:
                    # 其他错误，临时锁定cookie
                    cookie_rotator.report_cookie_status(account_id, False)
                
                return None
            
            # 如果请求成功，标记cookie为有效
            cookie_rotator.report_cookie_status(account_id, True)
            
            log.info(f"成功获取 {keywords_str} ({len(keywords)}个关键词) 的地域分布数据")
            return result
            
        except Exception as e:
            log.error(f"获取地域分布数据失败: {e}")
            # 如果是因为cookie问题，将其标记为无效
            if account_id:
                cookie_rotator.report_cookie_status(account_id, False)
            return None
    
    def _process_year_range(self, start_year, end_year):
        """处理年份范围，生成年度请求参数列表"""
        current_year = datetime.now().year
        
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
    
    def _generate_daily_date_ranges(self, start_date, end_date):
        """生成日度日期范围列表（每天一个日期范围）"""
        date_ranges = []
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        current = start
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            # 每天的范围就是当天到当天
            date_ranges.append((date_str, date_str))
            current += timedelta(days=1)
        
        return date_ranges
    
    def _process_task(self, task_data):
        """
        处理单个任务的函数，用于线程池
        
        参数:
            task_data (tuple): (keywords, region, start_date, end_date)
            其中 keywords 是关键词列表（虽然API不支持批量，但为了统一接口，仍然使用列表格式，但只包含一个关键词）
        
        返回值:
            (task_key, data_records, is_success) 其中 is_success 表示是否成功获取到有效数据
        """
        rate_limiter.wait()
        
        keywords, region, start_date, end_date = task_data
        
        # 确保只有一个关键词（地域分布API不支持批量）
        if len(keywords) > 1:
            log.warning(f"地域分布API不支持批量关键词，只处理第一个关键词: {keywords[0]}")
            keywords = [keywords[0]]
        
        keyword = keywords[0]
        
        # 生成任务键（用于检查点恢复）
        task_key = f"{keyword}_{region}_{start_date}_{end_date}"
        
        # 检查任务是否已完成（成功完成的任务跳过，失败的任务需要重试）
        if task_key in self.completed_task_keys:
            return None
        # 如果任务之前失败过，从失败集合中移除（准备重试）
        if task_key in self.failed_task_keys:
            with self.lock:
                self.failed_task_keys.discard(task_key)
        
        try:
            # 获取地域分布数据（单个关键词）
            result = self.get_region_distribution(
                keywords=[keyword],  # 只传递一个关键词
                region=region,
                days=None,  # 不使用days参数，使用start_date和end_date
                start_date=start_date,
                end_date=end_date
            )
            
            if not result:
                log.warning(f"获取数据失败，标记为失败任务: keyword={keyword}, region={region}, date={start_date} 至 {end_date}")
                # 返回失败标记，不保存空数据
                return task_key, None, False
            
            # 使用data_processor处理数据（单个关键词）
            df = data_processor.process_region_distribution_data(
                result, region, keyword, start_date, end_date
            )
            
            # 如果数据为空，标记为失败
            if df is None or len(df) == 0:
                log.warning(f"数据为空，标记为失败任务: keyword={keyword}, region={region}, date={start_date} 至 {end_date}")
                return task_key, None, False
            else:
                # 将DataFrame转换为字典列表，返回成功
                return task_key, df.to_dict('records'), True
            
        except Exception as e:
            log.error(f"处理任务时出错: {e}")
            log.error(traceback.format_exc())
            # 返回失败标记，不保存空数据
            return task_key, None, False
    
    def crawl(self, task_id=None, keywords=None, regions=None, days=None, start_date=None, end_date=None,
              date_ranges=None, year_range=None, output_format='csv', resume=True, checkpoint_task_id=None):
        """
        爬取多个关键词的地域分布数据
        
        参数:
            task_id (str): 任务ID，如果为None则自动生成
            keywords (list): 关键词列表
            regions (list): 地区代码列表，默认为[0]（全国）
            days (int): 预定义的天数，可以是7、30、90、180
            start_date (str): 开始日期，格式：YYYY-MM-DD
            end_date (str): 结束日期，格式：YYYY-MM-DD
            date_ranges (list): 日期范围列表，每个元素为 (start_date, end_date) 元组
            year_range (list/tuple): 年份范围，格式为 [start_year, end_year] 或 [[start_year, end_year]]
            output_format (str): 输出格式，可选值：csv, excel
            resume (bool): 是否从上次中断的地方继续爬取
            checkpoint_task_id (str): 检查点任务ID，如果为None则自动生成
        :return: 是否全部爬取成功
        """
        # 确保输入是列表
        if isinstance(keywords, str):
            if ',' in keywords:
                keywords = keywords.split(',')
            else:
                keywords = [keywords]
        
        if not keywords:
            log.error("未提供关键词列表")
            return False
        
        # 确保regions是列表
        if regions is None:
            regions = [0]  # 默认为全国
        elif not isinstance(regions, list):
            regions = [regions]
        
        # 转换地区代码为整数
        try:
            regions = [int(region) for region in regions]
        except (ValueError, TypeError):
            log.error("无效的地区代码")
            return False
        
        # 处理日期范围（和 search_index_crawler.py 一样的逻辑）
        log.info(f"爬虫接收到的 date_ranges 参数: {date_ranges}, 类型: {type(date_ranges)}, 长度: {len(date_ranges) if date_ranges else 0}")
        log.info(f"爬虫接收到的 year_range 参数: {year_range}, 类型: {type(year_range)}")
        log.info(f"爬虫接收到的 days 参数: {days}")
        log.info(f"爬虫接收到的 start_date 参数: {start_date}, end_date 参数: {end_date}")
        
        if date_ranges:
            # 直接使用传入的日期范围列表
            pass
        elif year_range:
            # 处理嵌套列表格式 [[start, end]] 或直接列表格式 [start, end]
            # 支持 list 和 tuple，支持字符串格式的年份
            log.info(f"处理 year_range: {year_range}, 类型: {type(year_range)}")
            if isinstance(year_range, (list, tuple)) and len(year_range) > 0:
                first_elem = year_range[0]
                log.info(f"year_range 首元素: {first_elem}, 类型: {type(first_elem)}")
                # 检查首元素是否也是序列 (list/tuple)，且长度>=2
                if isinstance(first_elem, (list, tuple)) and len(first_elem) >= 2:
                    # 嵌套格式 [[start, end]] 或 [["2023", "2025"]]
                    start_year = first_elem[0]
                    end_year = first_elem[1]
                    log.info(f"嵌套格式: start_year={start_year}, end_year={end_year}")
                    date_ranges = self._process_year_range(start_year, end_year)
                elif len(year_range) >= 2:
                    # 直接格式 [start, end] 或 ["2023", "2025"]
                    start_year = year_range[0]
                    end_year = year_range[1]
                    log.info(f"直接格式: start_year={start_year}, end_year={end_year}")
                    date_ranges = self._process_year_range(start_year, end_year)
                else:
                    log.warning(f"year_range 格式错误 (长度不足): {year_range}")
                    date_ranges = None
            else:
                log.warning(f"year_range 为空或格式错误: {year_range}")
                date_ranges = None
        elif days:
            # 使用预定义的天数
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days-1)).strftime('%Y-%m-%d')
            date_ranges = [(start_date, end_date)]
        elif start_date and end_date:
            # 使用明确的开始和结束日期，生成日度数据（每天一个请求）
            date_ranges = self._generate_daily_date_ranges(start_date, end_date)
        else:
            # 默认使用最近30天
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=29)).strftime('%Y-%m-%d')
            date_ranges = [(start_date, end_date)]
        
        # 如果经过上述处理后 date_ranges 仍为空，使用默认值
        if not date_ranges:
            log.info("未检测到有效的日期范围，使用默认最近30天")
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=29)).strftime('%Y-%m-%d')
            date_ranges = [(start_date, end_date)]
        
        log.info(f"最终使用的 date_ranges 长度: {len(date_ranges)}")
        
        # 确定任务ID
        self.task_id = task_id if task_id else datetime.now().strftime('%Y%m%d%H%M%S')
        task_id = self.task_id
        
        # 初始化任务状态
        checkpoint_status = None
        if resume and checkpoint_task_id:
            checkpoint_status = self._load_global_checkpoint(checkpoint_task_id)
            if checkpoint_status:
                log.info(f"从检查点恢复任务: {checkpoint_task_id}")
                self.completed_task_keys = set(checkpoint_status.get('completed_task_keys', []))
                self.completed_tasks = len(self.completed_task_keys)
            else:
                log.warning(f"未找到任务ID为 {checkpoint_task_id} 的检查点，将创建新任务")
                self.completed_task_keys = set()
                self.completed_tasks = 0
        else:
            self.completed_task_keys = set()
            self.completed_tasks = 0
        
        # 设置输出路径
        self.output_path = os.path.join(self.output_dir, task_id)
        os.makedirs(self.output_path, exist_ok=True)
        
        log.info(f"任务ID: {task_id}")
        log.info(f"开始爬取 {len(keywords)} 个关键词在 {len(regions)} 个地区的地域分布数据")
        
        # 地域分布API不支持批量关键词，必须一个关键词一个关键词请求
        log.info(f"地域分布API不支持批量请求，将逐个处理 {len(keywords)} 个关键词")
        
        # 准备所有任务（每个关键词单独一个任务）
        all_tasks = []
        for keyword in keywords:
            for region in regions:
                for date_start, date_end in date_ranges:
                    # 生成任务键（用于检查点恢复）
                    task_key = f"{keyword}_{region}_{date_start}_{date_end}"
                    
                    # 检查任务是否已完成
                    if task_key in self.completed_task_keys:
                        log.debug(f"跳过已完成的任务: {task_key}")
                        continue
                    
                    # 每个任务只包含一个关键词
                    all_tasks.append(([keyword], region, date_start, date_end))
        
        # 更新总任务数
        self.total_tasks = len(all_tasks)
        log.info(f"准备执行 {len(all_tasks)} 个任务，使用 {self.max_workers} 个线程")
        
        # 如果所有任务都已完成
        if not all_tasks:
            log.info("所有任务都已完成，无需执行")
            return True
        
        # 使用线程池执行任务
        executor = None
        try:
            executor = ThreadPoolExecutor(max_workers=self.max_workers)
            # 提交所有任务
            future_to_task = {executor.submit(self._process_task, task): task for task in all_tasks}
            
            # 收集本地缓存
            local_data_cache = []
            
            # 处理完成的任务
            for future in as_completed(future_to_task):
                # 检查退出标志
                if self._shutdown_flag:
                    log.warning("检测到退出标志，停止处理任务")
                    break
                
                try:
                    result = future.result()
                    if result:
                        # 解析返回值 - 新格式包含 is_success 标记
                        if len(result) == 3:
                            task_key, records, is_success = result
                        else:
                            # 兼容旧格式
                            task_key, records = result
                            is_success = records is not None and len(records) > 0
                        
                        if is_success and records:
                            # 成功：添加到本地缓存
                            local_data_cache.extend(records)
                            
                            # 更新全局任务状态
                            with self.lock:
                                self.completed_task_keys.add(task_key)
                                self.completed_tasks += 1
                                
                                # 每完成10个任务保存一次检查点
                                if self.completed_tasks % 10 == 0:
                                    self._save_global_checkpoint(task_id)
                            
                            # 定期保存数据（降低阈值，更频繁地保存）
                            if len(local_data_cache) >= 50:  # 降低阈值，从200改为50
                                with self.save_lock:
                                    self.data_cache.extend(local_data_cache)
                                    # 直接调用内部方法，避免重复获取锁
                                    self._save_data_cache_internal(force=True)
                                local_data_cache = []
                            
                            # 计算进度
                            total_processed = self.completed_tasks + self.failed_tasks
                            progress = 100.0 * total_processed / self.total_tasks if self.total_tasks > 0 else 0
                            log.info(f"进度: [{self.completed_tasks}/{self.total_tasks}] {progress:.2f}% - 已处理{len(records)}条数据记录")
                        else:
                            # 失败：标记为失败任务
                            with self.lock:
                                self.failed_task_keys.add(task_key)
                                self.failed_tasks += 1
                                log.warning(f"任务失败: {task_key}")
                        
                except Exception as e:
                    log.error(f"处理任务时出错: {e}")
                    log.error(traceback.format_exc())
            
            # 保存剩余的数据缓存（确保所有数据都被保存）
            if local_data_cache:
                log.info(f"保存剩余的 {len(local_data_cache)} 条数据记录")
                with self.save_lock:
                    self.data_cache.extend(local_data_cache)
                    # 直接调用内部方法，避免重复获取锁
                    self._save_data_cache_internal(force=True)
                local_data_cache = []
            
            # 最后再保存一次，确保所有数据都被保存
            with self.save_lock:
                if self.data_cache:
                    log.info(f"最终保存剩余的 {len(self.data_cache)} 条数据记录")
                    self._save_data_cache_internal(force=True)
            
            # 关闭线程池
            if executor:
                log.info("正在关闭线程池...")
                try:
                    executor.shutdown(wait=True)
                    log.info("线程池已关闭")
                except Exception as e:
                    log.warning(f"关闭线程池时出错: {e}")
                    executor.shutdown(wait=False)
        
        except KeyboardInterrupt:
            log.warning("收到键盘中断信号，正在保存数据...")
            # 保存剩余数据
            if 'local_data_cache' in locals() and local_data_cache:
                with self.save_lock:
                    self.data_cache.extend(local_data_cache)
                    self._save_data_cache_internal(force=True)
            # 关闭线程池
            if executor:
                executor.shutdown(wait=False)
            raise
        except Exception as e:
            log.error(f"任务执行过程中出错: {e}")
            log.error(traceback.format_exc())
            # 确保关闭线程池
            if executor:
                executor.shutdown(wait=False)
            return False
        
        # 更新任务完成状态
        with self.lock:
            # 判断任务是否应该标记为失败
            if self.failed_tasks > 0:
                # 有失败的任务，将整体任务标记为失败
                fail_rate = (self.failed_tasks / self.total_tasks * 100) if self.total_tasks > 0 else 0
                self.task_status[task_id] = {
                    'task_id': task_id,
                    'status': 'failed',
                    'total': self.total_tasks,
                    'completed': self.completed_tasks,
                    'failed': self.failed_tasks,
                    'progress': 100.0,
                    'completed_task_keys': list(self.completed_task_keys),
                    'failed_task_keys': list(self.failed_task_keys),
                    'output_file': self._get_output_path(task_id, output_format),
                    'error_message': f"任务执行完成但有 {self.failed_tasks} 个子任务失败（失败率: {fail_rate:.2f}%），需要重试"
                }
                
                # 保存最终检查点
                self._save_global_checkpoint(task_id)
                
                log.warning(f"任务完成但有失败项! 成功: {self.completed_tasks}, 失败: {self.failed_tasks}, 总计: {self.total_tasks}")
                
                return False
            else:
                # 全部成功完成
                self.task_status[task_id] = {
                    'task_id': task_id,
                    'status': 'completed',
                    'total': self.total_tasks,
                    'completed': self.completed_tasks,
                    'failed': 0,
                    'progress': 100.0,
                    'completed_task_keys': list(self.completed_task_keys),
                    'output_file': self._get_output_path(task_id, output_format)
                }
                
                # 保存最终检查点
                self._save_global_checkpoint(task_id)
                
                log.info(f"任务完成! 总共处理了 {self.completed_tasks}/{self.total_tasks} 个任务")
                
                return True
    
    def resume_task(self, task_id):
        """
        恢复指定的任务
        :param task_id: 任务ID
        :return: 是否成功恢复并完成任务
        """
        # 加载检查点
        checkpoint_status = self._load_global_checkpoint(task_id)
        if not checkpoint_status:
            log.error(f"无法恢复任务 {task_id}，检查点不存在")
            return False
        
        # 获取任务参数
        keywords = checkpoint_status.get('keywords', [])
        regions = checkpoint_status.get('regions', [0])
        days = checkpoint_status.get('days')
        start_date = checkpoint_status.get('start_date')
        end_date = checkpoint_status.get('end_date')
        date_ranges = checkpoint_status.get('date_ranges')
        year_range = checkpoint_status.get('year_range')
        output_format = checkpoint_status.get('output_format', 'csv')
        
        # 恢复任务
        return self.crawl(
            task_id=task_id,
            keywords=keywords, 
            regions=regions,
            days=days,
            start_date=start_date,
            end_date=end_date,
            date_ranges=date_ranges,
            year_range=year_range,
            output_format=output_format, 
            resume=True, 
            checkpoint_task_id=task_id
        )
    
    def get_task_status(self, task_id=None):
        """
        获取任务状态
        :param task_id: 任务ID，如果为None则返回最新的任务状态
        :return: 任务状态字典
        """
        with self.lock:
            if not self.task_status:
                return None
            
            if task_id is None:
                # 返回最新的任务状态
                return self.task_status[list(self.task_status.keys())[-1]]
            
            return self.task_status.get(task_id)
    
    def list_tasks(self):
        """
        列出所有任务
        :return: 任务摘要列表
        """
        tasks = []
        with self.lock:
            for task_id, status in self.task_status.items():
                tasks.append({
                    'task_id': task_id,
                    'status': status.get('status', 'unknown'),
                    'total': status.get('total', 0),
                    'completed': status.get('completed', 0),
                    'failed': status.get('failed', 0),
                    'progress': status.get('progress', 0),
                    'start_time': status.get('start_time'),
                    'last_update_time': status.get('last_update_time'),
                    'output_file': status.get('output_file')
                })
        return tasks


# 创建地域分布爬虫单例
region_distribution_crawler = RegionDistributionCrawler()


if __name__ == "__main__":
    # 示例用法
    keywords = ["电脑", "手机", "平板"]
    regions = [0, 916]  # 0表示全国，916表示江苏
    
    # 爬取数据
    region_distribution_crawler.crawl(keywords, regions=regions, days=30, output_format='csv', resume=True)
