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

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.logger import log
from utils.rate_limiter import rate_limiter
from utils.retry_decorator import retry
from utils.cipher_text import cipher_text_generator
from utils.data_processor import data_processor
from cookie_manager.cookie_rotator import cookie_rotator
from config.settings import BAIDU_INDEX_API, OUTPUT_DIR

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
        self.completed_keywords = set()  # 使用集合以加速查找
        self.current_keyword_index = 0
        self.current_city_index = 0
        self.current_date_range_index = 0
        self.city_dict = {}
        # 设置线程池最大工作线程数
        self.max_workers = 3
        # 修改为5个线程
        
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
    
    def _save_data_cache(self, status=None, force=False):
        """保存数据缓存到CSV文件"""
        with self.save_lock:
            data_count = 0
            stats_count = 0
            
            try:
                if (len(self.data_cache) >= self.cache_limit or force) and self.data_cache:
                    # 保存日度/周度数据
                    daily_df = pd.DataFrame(self.data_cache)
                    daily_path = os.path.join(self.output_path, f"search_index_{self.task_id}_daily_data.csv")
                    
                    # 记录实际保存的数据条数
                    data_count = len(daily_df)
                    
                    # 判断文件是否存在，决定是否写入表头
                    file_exists = os.path.isfile(daily_path)
                    daily_df.to_csv(daily_path, mode='a', header=not file_exists, index=False, encoding='utf-8-sig')
                    
                    # 清空缓存
                    self.data_cache = []
                    
                    # 显示进度信息
                    progress = 100.0 * self.completed_tasks / self.total_tasks if self.total_tasks > 0 else 0
                    log.info(f"进度: [{self.completed_tasks}/{self.total_tasks}] {progress:.2f}% - 已保存{data_count}条数据记录")
                    
                if (len(self.stats_cache) >= self.cache_limit or force) and self.stats_cache:
                    # 保存统计数据
                    stats_df = pd.DataFrame(self.stats_cache)
                    stats_path = os.path.join(self.output_path, f"search_index_{self.task_id}_stats_data.csv")
                    
                    # 记录实际保存的数据条数
                    stats_count = len(stats_df)
                    
                    # 判断文件是否存在，决定是否写入表头
                    file_exists = os.path.isfile(stats_path)
                    stats_df.to_csv(stats_path, mode='a', header=not file_exists, index=False, encoding='utf-8-sig')
                    
                    # 清空缓存
                    self.stats_cache = []
                
                # 如果是任务完成时的保存，更新统计数据
                if status == "completed":
                    try:
                        # 计算该任务的总爬取数据条数
                        total_crawled = 0
                        
                        # 计算日度数据文件的行数
                        daily_path = os.path.join(self.output_path, f"search_index_{self.task_id}_daily_data.csv")
                        if os.path.exists(daily_path):
                            with open(daily_path, 'r', encoding='utf-8-sig') as f:
                                total_crawled += sum(1 for _ in f) - 1  # 减去表头行
                        
                        # 获取当前日期
                        stat_date = datetime.now().date()
                        
                        # 连接数据库
                        from db.mysql_manager import MySQLManager
                        mysql = MySQLManager()
                        
                        # 查询当前任务信息
                        task_query = """
                            SELECT task_type FROM spider_tasks WHERE task_id = %s
                        """
                        task = mysql.fetch_one(task_query, (self.task_id,))
                        
                        if not task:
                            log.error(f"更新统计数据失败：任务 {self.task_id} 不存在")
                            return
                        
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
            except Exception as e:
                log.error(f"保存数据缓存时出现错误: {e}")
                log.error(traceback.format_exc())
    
    def _save_global_checkpoint(self):
        """保存全局检查点"""
        checkpoint = {
            'task_id': self.task_id,
            'completed_tasks': self.completed_tasks,
            'total_tasks': self.total_tasks,
            # 保存当前处理进度的详细信息
            'completed_keywords': self.completed_keywords,
            'current_keyword_index': self.current_keyword_index,
            'current_city_index': self.current_city_index,
            'current_date_range_index': self.current_date_range_index,
            # 保存任务配置信息，用于恢复时重建任务上下文
            'city_dict': self.city_dict,
            'output_path': self.output_path,
            'save_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(self.checkpoint_path, 'wb') as f:
            pickle.dump(checkpoint, f)
        # log.info(f"检查点已保存: {self.checkpoint_path}, 已完成任务: {self.completed_tasks}/{self.total_tasks}")
        
    def _load_global_checkpoint(self, task_id):
        """加载全局检查点"""
        self.task_id = task_id
        self.checkpoint_path = os.path.join(OUTPUT_DIR, f"checkpoints/search_index_checkpoint_{self.task_id}.pkl")
        
        # 确保检查点目录存在
        os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)
        
        if os.path.exists(self.checkpoint_path):
            try:
                with open(self.checkpoint_path, 'rb') as f:
                    checkpoint = pickle.load(f)
                    # 显式设置完成任务数和总任务数
                    self.completed_tasks = checkpoint.get('completed_tasks', 0)
                    self.total_tasks = checkpoint.get('total_tasks', 0)
                    # 加载已完成的关键词和城市索引信息
                    self.completed_keywords = checkpoint.get('completed_keywords', set())
                    self.current_keyword_index = checkpoint.get('current_keyword_index', 0)
                    self.current_city_index = checkpoint.get('current_city_index', 0)
                    self.current_date_range_index = checkpoint.get('current_date_range_index', 0)
                    # 加载任务配置信息
                    self.city_dict = checkpoint.get('city_dict', {})
                    self.output_path = checkpoint.get('output_path', os.path.join(OUTPUT_DIR, 'search_index', self.task_id))
                    
                log.info(f"已加载检查点: {self.checkpoint_path}, 已完成任务: {self.completed_tasks}/{self.total_tasks}")
                log.info(f"已完成的任务项: {len(self.completed_keywords)}, 恢复时将跳过这些任务")
                return True
            except Exception as e:
                log.error(f"加载检查点文件失败: {e}")
                log.error(traceback.format_exc())
                # 加载失败时重置计数器
                self.completed_tasks = 0
                self.total_tasks = 0
                return False
        # 如果检查点不存在，确保计数器为0
        self.completed_tasks = 0
        self.total_tasks = 0
        return False

    def _update_ab_sr_cookies(self):
        """更新所有账号的ab_sr cookie"""
        try:
            log.info("开始更新所有账号的ab_sr cookie...")
            # 导入需要的模块
            from cookie_manager.cookie_manager import CookieManager
            
            # 创建Cookie管理器
            cookie_manager = CookieManager()
            
            # 更新所有账号的ab_sr cookie
            result = cookie_manager.update_ab_sr_for_all_accounts()
            
            # 关闭Cookie管理器连接
            cookie_manager.close()
            
            if 'error' in result:
                log.error(f"更新ab_sr cookie失败: {result['error']}")
                return False
            
            log.info(f"成功更新ab_sr cookie: 更新{result['updated_count']}个，新增{result['added_count']}个，失败{result['failed_count']}个")
            
            # 更新完成后重置cookie轮换器的缓存
            self.cookie_rotator.reset_cache()
            
            return True
        except Exception as e:
            log.error(f"更新ab_sr cookie时出错: {e}")
            log.error(traceback.format_exc())
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
        # 使用rate_limiter来限制请求频率 - 注释掉这行，不再等待
        # rate_limiter.wait()
        
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
            # 修改这里：不再等待，而是抛出特定异常，以便上层处理
            log.warning("所有Cookie均被锁定，无法继续爬取")
            raise NoCookieAvailableError("所有Cookie均被锁定，无法继续爬取")
            
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
        """
        rate_limiter.wait()
        keyword, city_code, city_name, start_date, end_date = task_data
        
        # 检查任务是否已完成
        task_key = f"{keyword}_{city_code}_{start_date}_{end_date}"
        if task_key in self.completed_keywords:
            # 如果任务已完成，直接返回None，不增加completed_tasks计数
            return None
            
        # log.info(f"正在处理任务: {task_key}")
        
        try:
            # 获取数据
            result = self._get_search_index(city_code, [keyword], start_date, end_date)
            if not result:
                log.warning(f"获取数据失败，跳过当前任务: {task_key}")
                # 构造空结果
                empty_daily_data = [{
                    '关键词': keyword,
                    '城市代码': city_code,
                    '城市': city_name,
                    '日期': start_date,
                    '数据类型': '日度',
                    '数据间隔(天)': 1,
                    '所属年份': start_date[:4],
                    'PC+移动指数': '0',
                    '移动指数': '0',
                    'PC指数': '0',
                    '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }]
                
                empty_stats_record = {
                    '关键词': keyword,
                    '城市代码': city_code,
                    '城市': city_name,
                    '时间范围': f"{start_date} 至 {end_date}",
                    '整体日均值': 0,
                    '整体同比': '-',
                    '整体环比': '-',
                    '移动日均值': 0,
                    '移动同比': '-',
                    '移动环比': '-',
                    'PC日均值': 0,
                    'PC同比': '-',
                    'PC环比': '-',
                    '整体总值': 0,
                    '移动总值': 0,
                    'PC总值': 0,
                    '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                return task_key, empty_daily_data, empty_stats_record
        except NoCookieAvailableError:
            # 向上层抛出异常，通知主线程暂停任务
            raise
        except Exception as e:
            log.error(f"处理任务 {task_key} 时出错: {e}")
            # 构造空结果
            empty_daily_data = [{
                '关键词': keyword,
                '城市代码': city_code,
                '城市': city_name,
                '日期': start_date,
                '数据类型': '日度',
                '数据间隔(天)': 1,
                '所属年份': start_date[:4],
                'PC+移动指数': '0',
                '移动指数': '0',
                'PC指数': '0',
                '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }]
            
            empty_stats_record = {
                '关键词': keyword,
                '城市代码': city_code,
                '城市': city_name,
                '时间范围': f"{start_date} 至 {end_date}",
                '整体日均值': 0,
                '整体同比': '-',
                '整体环比': '-',
                '移动日均值': 0,
                '移动同比': '-',
                '移动环比': '-',
                'PC日均值': 0,
                'PC同比': '-',
                'PC环比': '-',
                '整体总值': 0,
                '移动总值': 0,
                'PC总值': 0,
                '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return task_key, empty_daily_data, empty_stats_record
            
        data, cookie = result
        
        # 处理数据
        daily_data, stats_record = self._process_search_index_data(
            data, cookie, keyword, city_code, city_name, start_date, end_date
        )
        
        # 如果处理结果为None，构造空结果
        if daily_data is None or stats_record is None:
            log.warning(f"处理数据失败，构造空结果: {task_key}")
            empty_daily_data = [{
                '关键词': keyword,
                '城市代码': city_code,
                '城市': city_name,
                '日期': start_date,
                '数据类型': '日度',
                '数据间隔(天)': 1,
                '所属年份': start_date[:4],
                'PC+移动指数': '0',
                '移动指数': '0',
                'PC指数': '0',
                '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }]
            
            empty_stats_record = {
                '关键词': keyword,
                '城市代码': city_code,
                '城市': city_name,
                '时间范围': f"{start_date} 至 {end_date}",
                '整体日均值': 0,
                '整体同比': '-',
                '整体环比': '-',
                '移动日均值': 0,
                '移动同比': '-',
                '移动环比': '-',
                'PC日均值': 0,
                'PC同比': '-',
                'PC环比': '-',
                '整体总值': 0,
                '移动总值': 0,
                'PC总值': 0,
                '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return task_key, empty_daily_data, empty_stats_record
        
        return task_key, daily_data, stats_record

    
    def crawl(self, task_id=None, keywords=None, cities=None, date_ranges=None, days=None, 
              keywords_file=None, cities_file=None, date_ranges_file=None,
              year_range=None, resume=False, checkpoint_task_id=None, total_tasks=None):
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
            # 重置任务计数器
            self.completed_tasks = 0
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
        
        # 上次进度更新的百分比
        last_progress_percent = 0
        
        # 记录上次更新ab_sr的任务数
        last_ab_sr_update_task_count = 0
        
        # 开始爬取前先更新一次ab_sr cookie
        self._update_ab_sr_cookies()
        
        # 开始爬取
        try:
            # 准备所有任务
            all_tasks = []
            for keyword in keywords:
                for city_code, city_name in self.city_dict.items():
                    for start_date, end_date in date_ranges:
                        task_key = f"{keyword}_{city_code}_{start_date}_{end_date}"
                        # 检查任务是否已完成
                        if task_key in self.completed_keywords:
                            log.debug(f"跳过已完成的任务: {task_key}")
                            continue
                        all_tasks.append((keyword, city_code, city_name, start_date, end_date))
            
            # 更新实际总任务数为需要执行的任务数量
            # self.total_tasks = len(all_tasks)
            log.info(f"准备执行 {len(all_tasks)} 个任务，使用 {self.max_workers} 个线程")
            
            # 如果所有任务都已完成
            if not all_tasks:
                log.info("所有任务都已完成，无需执行")
                # 更新数据库中的最终状态
                try:
                    from db.mysql_manager import MySQLManager
                    mysql = MySQLManager()
                    
                    update_query = """
                        UPDATE spider_tasks 
                        SET progress = 100, completed_items = %s, status = 'completed', update_time = %s, end_time = %s
                        WHERE task_id = %s
                    """
                    now = datetime.now()
                    mysql.execute_query(update_query, (self.total_tasks, now, now, self.task_id))
                    
                    log.info(f"任务完成! 总共处理了 {self.completed_tasks}/{self.total_tasks} 个任务")
                except Exception as e:
                    log.error(f"更新最终任务状态失败: {e}")
                
                return True
            
            # 使用线程池执行任务
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有任务
                future_to_task = {executor.submit(self._process_task, task): task for task in all_tasks}
                
                # 收集本地缓存
                local_data_cache = []
                local_stats_cache = []
                
                # 处理完成的任务
                try:
                    for future in as_completed(future_to_task):
                        try:
                            result = future.result()
                            if result:
                                task_key, daily_data, stats_record = result
                                
                                # 确保 daily_data 和 stats_record 不为 None
                                if daily_data is not None and stats_record is not None:
                                    # 添加到本地缓存
                                    local_data_cache.extend(daily_data)
                                    local_stats_cache.append(stats_record)
                                    
                                    # 更新全局任务状态
                                    with self.task_lock:
                                        self.completed_keywords.add(task_key)
                                        self.completed_tasks += 1
                                        # 每完成10个任务保存一次检查点
                                        if self.completed_tasks % 10 == 0:
                                            self._save_global_checkpoint()
                                    
                                    # 定期保存数据
                                    if len(local_data_cache) >= 100:
                                        with self.save_lock:
                                            self._save_data_to_file(local_data_cache, local_stats_cache)
                                        local_data_cache = []
                                        local_stats_cache = []
                                    
                                    # 计算当前进度百分比
                                    current_progress_percent = int((self.completed_tasks / self.total_tasks) * 100)
                                    
                                    # 每完成5%的任务更新一次数据库进度
                                    if current_progress_percent >= last_progress_percent + 5:
                                        last_progress_percent = current_progress_percent
                                        try:
                                            # 连接数据库
                                            from db.mysql_manager import MySQLManager
                                            mysql = MySQLManager()
                                            
                                            # 更新任务进度
                                            update_query = """
                                                UPDATE spider_tasks 
                                                SET progress = %s, completed_items = %s, update_time = %s
                                                WHERE task_id = %s
                                            """
                                            affected_rows = mysql.execute_query(
                                                update_query, 
                                                (min(current_progress_percent, 100), self.completed_tasks, datetime.now(), self.task_id)
                                            )
                                            
                                            if affected_rows > 0:
                                                log.info(f"已更新数据库进度: {min(current_progress_percent, 100)}%, 完成任务: {self.completed_tasks}/{self.total_tasks}")
                                            else:
                                                log.warning(f"数据库进度更新失败: 影响行数为0, task_id: {self.task_id}")
                                                
                                                # 检查任务是否存在
                                                check_query = "SELECT id FROM spider_tasks WHERE task_id = %s"
                                                task = mysql.fetch_one(check_query, (self.task_id,))
                                                if task:
                                                    log.info(f"任务存在于数据库中, ID: {task['id']}")
                                                else:
                                                    log.error(f"任务不存在于数据库中: {self.task_id}")
                                        except Exception as e:
                                            log.error(f"更新数据库进度失败: {e}")
                                            log.error(traceback.format_exc())
                                    
                                    # 每完成10条任务更新一次ab_sr cookie
                                    if self.completed_tasks - last_ab_sr_update_task_count >= 10:
                                        log.info(f"已完成{self.completed_tasks}条任务，开始更新ab_sr cookie...")
                                        self._update_ab_sr_cookies()
                                        last_ab_sr_update_task_count = self.completed_tasks
                                else:
                                    log.warning(f"任务 {task_key} 返回了无效的数据结构")
                                    
                        except NoCookieAvailableError:
                            # 处理没有可用Cookie的情况
                            log.error("没有可用的Cookie，暂停任务并保存当前进度")
                            
                            # 保存当前进度
                            self._save_data_cache(force=True)
                            self._save_global_checkpoint()
                            
                            # 更新数据库中的任务状态为暂停
                            try:
                                from db.mysql_manager import MySQLManager
                                mysql = MySQLManager()
                                
                                update_query = """
                                    UPDATE spider_tasks 
                                    SET status = 'paused', progress = %s, completed_items = %s, 
                                        error_message = %s, update_time = %s
                                    WHERE task_id = %s
                                """
                                progress = min(int((self.completed_tasks / self.total_tasks) * 100) if self.total_tasks > 0 else 0, 100)
                                mysql.execute_query(
                                    update_query, 
                                    (progress, self.completed_tasks, "所有Cookie均被锁定，任务暂停等待可用Cookie", datetime.now(), self.task_id)
                                )
                                
                                log.info(f"任务已暂停，等待Cookie可用: {self.task_id}")
                            except Exception as e:
                                log.error(f"更新任务状态失败: {e}")
                            
                            # 取消所有未完成的任务
                            for f in future_to_task:
                                if not f.done() and not f.cancelled():
                                    f.cancel()
                            
                            # 提前返回，等待定时任务恢复
                            return False
                            
                        except Exception as e:
                            log.error(f"处理任务时出错: {e}")
                            log.error(traceback.format_exc())
                
                    # 保存剩余的数据
                    if local_data_cache:
                        with self.save_lock:
                            self._save_data_to_file(local_data_cache, local_stats_cache)
                
                except Exception as e:
                    log.error(f"任务执行过程中出错: {e}")
                    log.error(traceback.format_exc())
                    
                    # 保存当前进度
                    self._save_data_cache(force=True)
                    self._save_global_checkpoint()
                    print(e)
                    # 如果是NoCookieAvailableError，更新任务状态为暂停
                    if isinstance(e, NoCookieAvailableError):
                        print("NoCookieAvailableError")
                        try:
                            from db.mysql_manager import MySQLManager
                            mysql = MySQLManager()
                            
                            update_query = """
                                UPDATE spider_tasks 
                                SET status = 'paused', progress = %s, completed_items = %s, 
                                    error_message = %s, update_time = %s
                                WHERE task_id = %s
                            """
                            progress = min(int((self.completed_tasks / self.total_tasks) * 100) if self.total_tasks > 0 else 0, 100)
                            mysql.execute_query(
                                update_query, 
                                (progress, self.completed_tasks, "所有Cookie均被锁定，任务暂停等待可用Cookie", datetime.now(), self.task_id)
                            )
                            
                            log.info(f"任务已暂停，等待Cookie可用: {self.task_id}")
                        except Exception as db_error:
                            log.error(f"更新任务状态失败: {db_error}")
                        
                        return False
                    else:
                        print("else")
                        # 只有非Cookie问题才标记为失败
                        try:
                            from db.mysql_manager import MySQLManager
                            mysql = MySQLManager()
                            
                            update_query = """
                                UPDATE spider_tasks 
                                SET status = 'failed', progress = %s, completed_items = %s, 
                                    error_message = %s, update_time = %s
                                WHERE task_id = %s
                            """
                            progress = min(int((self.completed_tasks / self.total_tasks) * 100) if self.total_tasks > 0 else 0, 100)
                            mysql.execute_query(
                                update_query, 
                                (progress, self.completed_tasks, f"任务执行出错: {str(e)[:500]}", datetime.now(), self.task_id)
                            )
                            
                            log.error(f"任务执行失败: {self.task_id}")
                        except Exception as db_error:
                            log.error(f"更新任务状态失败: {db_error}")
                        
                        return False
            
            # 最后保存所有剩余数据和检查点
            self._save_data_cache(status="completed", force=True)
            self._save_global_checkpoint()
            
            # 更新数据库中的最终状态
            try:
                from db.mysql_manager import MySQLManager
                mysql = MySQLManager()
                
                # 确保进度不超过100%
                final_progress = 100
                final_completed = min(self.completed_tasks, self.total_tasks)
                
                update_query = """
                    UPDATE spider_tasks 
                    SET progress = %s, completed_items = %s, status = 'completed', update_time = %s, end_time = %s
                    WHERE task_id = %s
                """
                now = datetime.now()
                mysql.execute_query(update_query, (final_progress, final_completed, now, now, self.task_id))
                
                log.info(f"任务完成! 总共处理了 {self.completed_tasks}/{self.total_tasks} 个任务")
            except Exception as e:
                log.error(f"更新最终任务状态失败: {e}")
            
            return True
            
        except Exception as e:
            log.error(f"爬取过程中出错: {str(e)}")
            log.error(traceback.format_exc())
            # 保存当前进度和数据
            self._save_data_cache(force=True)
            self._save_global_checkpoint()
            
            # 更新数据库中的错误状态
            try:
                from db.mysql_manager import MySQLManager
                mysql = MySQLManager()
                
                # 如果是NoCookieAvailableError，更新任务状态为暂停
                if isinstance(e, NoCookieAvailableError):
                    update_query = """
                        UPDATE spider_tasks 
                        SET status = 'paused', progress = %s, completed_items = %s, 
                            error_message = %s, update_time = %s
                        WHERE task_id = %s
                    """
                    error_message = "所有Cookie均被锁定，任务暂停等待可用Cookie"
                    
                    progress = min(int((self.completed_tasks / self.total_tasks) * 100) if self.total_tasks > 0 else 0, 100)
                    mysql.execute_query(
                        update_query, 
                        (progress, self.completed_tasks, error_message, datetime.now(), self.task_id)
                    )
                    
                    log.info(f"任务已暂停，等待Cookie可用: {self.task_id}")
                else:
                    update_query = """
                        UPDATE spider_tasks 
                        SET progress = %s, completed_items = %s, status = 'failed', 
                            error_message = %s, update_time = %s
                        WHERE task_id = %s
                    """
                    error_message = str(e)[:500]
                    
                    progress = min(int((self.completed_tasks / self.total_tasks) * 100) if self.total_tasks > 0 else 0, 100)
                    mysql.execute_query(
                        update_query, 
                        (progress, self.completed_tasks, error_message, datetime.now(), self.task_id)
                    )
                    
                    log.error(f"任务执行失败: {self.task_id}")
            except Exception as db_error:
                log.error(f"更新任务错误状态失败: {db_error}")
                
            # 如果是NoCookieAvailableError，返回False但不视为失败
            if isinstance(e, NoCookieAvailableError):
                return False
            else:
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
            from db.mysql_manager import MySQLManager
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

    def _save_data_to_file(self, data_cache, stats_cache):
        """保存本地缓存数据到文件"""
        try:
            if data_cache:
                # 保存日度/周度数据
                daily_df = pd.DataFrame(data_cache)
                daily_path = os.path.join(self.output_path, f"search_index_{self.task_id}_daily_data.csv")
                
                # 记录实际保存的数据条数
                data_count = len(daily_df)
                
                # 判断文件是否存在，决定是否写入表头
                file_exists = os.path.isfile(daily_path)
                daily_df.to_csv(daily_path, mode='a', header=not file_exists, index=False, encoding='utf-8-sig')
                
                # 显示进度信息
                progress = 100.0 * self.completed_tasks / self.total_tasks if self.total_tasks > 0 else 0
                log.info(f"进度: [{self.completed_tasks}/{self.total_tasks}] {progress:.2f}% - 已保存{data_count}条数据记录")
                
            if stats_cache:
                # 保存统计数据
                stats_df = pd.DataFrame(stats_cache)
                stats_path = os.path.join(self.output_path, f"search_index_{self.task_id}_stats_data.csv")
                
                # 判断文件是否存在，决定是否写入表头
                file_exists = os.path.isfile(stats_path)
                stats_df.to_csv(stats_path, mode='a', header=not file_exists, index=False, encoding='utf-8-sig')
            
            # 同时保存检查点，确保数据一致性
            if data_cache or stats_cache:
                self._save_global_checkpoint()
                
        except Exception as e:
            log.error(f"保存数据到文件时出错: {e}")
            log.error(traceback.format_exc())

# 创建爬虫实例
search_index_crawler = SearchIndexCrawler()

 