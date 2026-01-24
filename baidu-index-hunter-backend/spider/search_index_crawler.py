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
        from db.config_manager import config_manager
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
                            
                            # log.info(f"更新累计爬取数据条数: {current_total_crawled} -> {new_total_crawled} (新增: {total_crawled})")
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
        # 将集合转换为列表，以避免序列化大型集合时的问题
        completed_keywords_list = list(self.completed_keywords) if isinstance(self.completed_keywords, set) else self.completed_keywords
        
        # 如果列表过大，分批保存
        if len(completed_keywords_list) > 2500:
            # 将列表分成多个块
            chunk_size = 2500
            chunks = [completed_keywords_list[i:i + chunk_size] for i in range(0, len(completed_keywords_list), chunk_size)]
            
            # 保存主检查点
            checkpoint = {
                'task_id': self.task_id,
                'completed_tasks': self.completed_tasks,
                'total_tasks': self.total_tasks,
                # 只保存一个标志，表明关键词被分块了
                'completed_keywords_chunked': True,
                'chunks_count': len(chunks),
                # 保存当前处理进度的详细信息
                'current_keyword_index': self.current_keyword_index,
                'current_city_index': self.current_city_index,
                'current_date_range_index': self.current_date_range_index,
                # 保存任务配置信息，用于恢复时重建任务上下文
                'city_dict': self.city_dict,
                'output_path': self.output_path,
                'save_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 保存主检查点
            with open(self.checkpoint_path, 'wb') as f:
                pickle.dump(checkpoint, f)
            
            # 保存分块数据
            for i, chunk in enumerate(chunks):
                chunk_path = f"{self.checkpoint_path}.chunk{i}"
                with open(chunk_path, 'wb') as f:
                    pickle.dump(chunk, f)
                log.debug(f"保存分块文件: {chunk_path}, 包含 {len(chunk)} 个关键词")
            
            # log.info(f"检查点已分块保存: {self.checkpoint_path}, 共{len(chunks)}个块, 每块大小约{chunk_size}个关键词, 已完成任务: {self.completed_tasks}/{self.total_tasks}")
        else:
            # 如果数据量不大，正常保存
            checkpoint = {
                'task_id': self.task_id,
                'completed_tasks': self.completed_tasks,
                'total_tasks': self.total_tasks,
                # 保存当前处理进度的详细信息
                'completed_keywords': completed_keywords_list,
                'completed_keywords_chunked': False,
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
            
            # log.info(f"检查点已保存: {self.checkpoint_path}, 包含 {len(completed_keywords_list)} 个关键词, 已完成任务: {self.completed_tasks}/{self.total_tasks}")
    
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
                
                # 检查是否使用了分块存储
                if checkpoint.get('completed_keywords_chunked', False):
                    # 从分块文件中加载关键词
                    completed_keywords_list = []
                    
                    # 获取检查点目录中所有的分块文件
                    checkpoint_dir = os.path.dirname(self.checkpoint_path)
                    chunk_prefix = f"{os.path.basename(self.checkpoint_path)}.chunk"
                    chunk_files = [f for f in os.listdir(checkpoint_dir) if f.startswith(chunk_prefix)]
                    
                    if not chunk_files:
                        # 如果没有找到分块文件，尝试使用chunks_count
                        chunks_count = checkpoint.get('chunks_count', 0)
                        log.warning(f"未找到分块文件，尝试使用chunks_count={chunks_count}加载")
                        
                        for i in range(chunks_count):
                            chunk_path = f"{self.checkpoint_path}.chunk{i}"
                            if os.path.exists(chunk_path):
                                try:
                                    with open(chunk_path, 'rb') as f:
                                        chunk = pickle.load(f)
                                        completed_keywords_list.extend(chunk)
                                        log.info(f"加载分块文件: {chunk_path}, 包含 {len(chunk)} 个关键词")
                                except Exception as e:
                                    log.error(f"加载关键词分块文件失败: {chunk_path}, 错误: {e}")
                    else:
                        # 按照分块文件名排序并加载
                        chunk_files.sort()
                        log.info(f"发现 {len(chunk_files)} 个分块文件")
                        
                        for chunk_file in chunk_files:
                            chunk_path = os.path.join(checkpoint_dir, chunk_file)
                            try:
                                with open(chunk_path, 'rb') as f:
                                    chunk = pickle.load(f)
                                    completed_keywords_list.extend(chunk)
                                    log.info(f"加载分块文件: {chunk_file}, 包含 {len(chunk)} 个关键词")
                            except Exception as e:
                                log.error(f"加载关键词分块文件失败: {chunk_path}, 错误: {e}")
                    
                    # 转换为集合
                    self.completed_keywords = set(completed_keywords_list)
                    
                    # 更新主检查点中的chunks_count
                    actual_chunks_count = len(chunk_files) if chunk_files else checkpoint.get('chunks_count', 0)
                    if actual_chunks_count != checkpoint.get('chunks_count', 0):
                        log.warning(f"检查点中的chunks_count({checkpoint.get('chunks_count', 0)})与实际找到的分块文件数量({actual_chunks_count})不一致")
                        checkpoint['chunks_count'] = actual_chunks_count
                        
                        # 保存更新后的主检查点
                        with open(self.checkpoint_path, 'wb') as f:
                            pickle.dump(checkpoint, f)
                        log.info(f"已更新主检查点的chunks_count为: {actual_chunks_count}")
                else:
                    # 直接从检查点加载
                    completed_keywords = checkpoint.get('completed_keywords', [])
                    self.completed_keywords = set(completed_keywords) if isinstance(completed_keywords, list) else completed_keywords
                
                # 加载其他索引信息
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
                self.completed_keywords = set()
                return False
        
        # 如果检查点不存在，确保计数器为0
        self.completed_tasks = 0
        self.total_tasks = 0
        self.completed_keywords = set()
        return False

    def _update_ab_sr_cookies(self):
        """更新所有账号的ab_sr cookie"""
        try:
            # log.info("开始更新所有账号的ab_sr cookie...")
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
            
            # log.info(f"成功更新ab_sr cookie: 更新{result['updated_count']}个，新增{result['added_count']}个，失败{result['failed_count']}个")
            
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
            'Referer': 'https://index.baidu.com/v2/main/index.html',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': BAIDU_INDEX_API['user_agent'],
            'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
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
        """处理搜索指数数据（单个关键词）"""
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

    def _process_multi_search_index_data(self, data, cookie, keywords, city_code, city_name, start_date, end_date):
        """
        处理多个关键词的搜索指数数据
        :param data: API返回的原始数据
        :param cookie: 用于请求的cookie
        :param keywords: 关键词列表
        :param city_code: 城市代码
        :param city_name: 城市名称
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: (daily_data_list, stats_record_list) 元组，分别为日度数据列表和统计数据记录列表的列表
        """
        if not data or not data.get('data') or not data['data'].get('userIndexes'):
            log.warning(f"数据为空或格式不正确: {data}")
            return [], []
            
        try:
            # 获取uniqid用于解密
            uniqid = data['data']['uniqid']
            
            # 获取解密密钥
            key = self._get_key(uniqid, cookie)
            if not key:
                log.error("获取解密密钥失败")
                return [], []
            
            # 用于存储每个关键词的处理结果
            all_daily_data = []
            all_stats_records = []
            
            # 确保用户索引和关键词列表长度一致
            user_indexes = data['data']['userIndexes']
            general_ratio = data['data']['generalRatio']
            
            # 检查数据完整性
            if len(user_indexes) != len(keywords) or len(general_ratio) != len(keywords):
                log.warning(f"关键词数量与返回的数据不匹配: keywords={len(keywords)}, userIndexes={len(user_indexes)}, generalRatio={len(general_ratio)}")
                
                # 为缺少的关键词构造空数据
                if len(user_indexes) < len(keywords):
                    # 构造空的用户索引数据
                    empty_user_index = {
                        'all': {'data': []},
                        'wise': {'data': []},
                        'pc': {'data': []}
                    }
                    # 补充缺少的用户索引数据
                    for _ in range(len(keywords) - len(user_indexes)):
                        user_indexes.append(empty_user_index.copy())
                
                if len(general_ratio) < len(keywords):
                    # 构造空的比例数据
                    empty_ratio = {'status': 0, 'all': 0, 'pc': 0, 'wise': 0}
                    # 补充缺少的比例数据
                    for _ in range(len(keywords) - len(general_ratio)):
                        general_ratio.append(empty_ratio.copy())
                
                # 确保数据长度一致
                max_length = len(keywords)
                if len(user_indexes) > max_length:
                    user_indexes = user_indexes[:max_length]
                if len(general_ratio) > max_length:
                    general_ratio = general_ratio[:max_length]
                
                log.info(f"数据补齐后: keywords={len(keywords)}, userIndexes={len(user_indexes)}, generalRatio={len(general_ratio)}")
            
            # 处理每个关键词的数据
            for i, keyword in enumerate(keywords):
                try:
                    # 获取各终端数据，确保即使数据为空也能创建默认值
                    all_data = user_indexes[i]['all']['data'] if i < len(user_indexes) and 'all' in user_indexes[i] and 'data' in user_indexes[i]['all'] else ''
                    wise_data = user_indexes[i]['wise']['data'] if i < len(user_indexes) and 'wise' in user_indexes[i] and 'data' in user_indexes[i]['wise'] else ''
                    pc_data = user_indexes[i]['pc']['data'] if i < len(user_indexes) and 'pc' in user_indexes[i] and 'data' in user_indexes[i]['pc'] else ''
                    
                    # 解密数据
                    decrypted_all = self._decrypt(key, all_data)
                    decrypted_wise = self._decrypt(key, wise_data)
                    decrypted_pc = self._decrypt(key, pc_data)
                    # print("key",key)
                    # print("all_data",all_data)
                    # print("decrypted_all",decrypted_all)
                    
                    # 创建单个关键词的数据
                    single_data = {
                        'data': {
                            'userIndexes': [user_indexes[i] if i < len(user_indexes) else {'all': {'data': []}, 'wise': {'data': []}, 'pc': {'data': []}}],
                            'generalRatio': [general_ratio[i] if i < len(general_ratio) else {'status': 0, 'all': 0, 'pc': 0, 'wise': 0}],
                            'uniqid': uniqid
                        },
                        'status': 0
                    }
                    
                    # 检查解密后的数据是否为空
                    all_values = decrypted_all.split(',') if decrypted_all else []
                    wise_values = decrypted_wise.split(',') if decrypted_wise else []
                    pc_values = decrypted_pc.split(',') if decrypted_pc else []
                    
                    # 如果所有数据都为空，直接创建默认数据
                    if len(all_values) == 0 and len(wise_values) == 0 and len(pc_values) == 0:
                        # log.warning(f"关键词 '{keyword}' 的解密数据为空，创建默认数据")
                        default_daily_data = [{
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
                        
                        default_stats_record = {
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
                        
                        all_daily_data.extend(default_daily_data)
                        all_stats_records.append(default_stats_record)
                        continue
                    
                    # 调用data_processor处理数据
                    daily_data, stats_record = data_processor.process_search_index_daily_data(
                        single_data, cookie, keyword, city_code, city_name, 
                        start_date, end_date, decrypted_all, decrypted_wise, decrypted_pc
                    )
                    
                    # 如果处理结果为空，创建默认的空数据
                    if not daily_data or not stats_record:
                        log.warning(f"为关键词 '{keyword}' 创建默认空数据")
                        
                        # 创建默认的日度数据
                        default_daily_data = [{
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
                        
                        # 创建默认的统计数据
                        default_stats_record = {
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
                        
                        all_daily_data.extend(default_daily_data)
                        all_stats_records.append(default_stats_record)
                    else:
                        all_daily_data.extend(daily_data)
                        all_stats_records.append(stats_record)
                    
                except Exception as e:
                    log.error(f"处理关键词 '{keyword}' 的数据时出错: {e}")
                    # 创建默认的空数据
                    default_daily_data = [{
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
                    
                    default_stats_record = {
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
                    
                    all_daily_data.extend(default_daily_data)
                    all_stats_records.append(default_stats_record)
                    continue
            
            # 确保即使处理结果为空，也返回有效的数据
            if not all_daily_data or not all_stats_records:
                log.warning(f"处理后没有有效数据，为所有关键词创建默认数据")
                all_daily_data = []
                all_stats_records = []
                
                for keyword in keywords:
                    all_daily_data.append({
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
                    })
                    
                    all_stats_records.append({
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
                    })
            
            return all_daily_data, all_stats_records
            
        except Exception as e:
            log.error(f"处理多关键词搜索指数数据时出错: {str(e)}")
            log.error(traceback.format_exc())
            
            # 出错时也创建默认数据
            all_daily_data = []
            all_stats_records = []
            
            for keyword in keywords:
                all_daily_data.append({
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
                })
                
                all_stats_records.append({
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
                })
            
            return all_daily_data, all_stats_records
    
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
        
        # 检查任务是否已完成
        if not is_batch:
            task_key = f"{keyword}_{city_code}_{start_date}_{end_date}"
            if task_key in self.completed_keywords:
                # 如果任务已完成，直接返回None，不增加completed_tasks计数
                return None
        else:
            # 批量模式下，检查所有关键词是否都已完成
            all_completed = True
            for keyword in keywords:
                task_key = f"{keyword}_{city_code}_{start_date}_{end_date}"
                if task_key not in self.completed_keywords:
                    all_completed = False
                    break
            
            if all_completed:
                return None
        
        try:
            # 获取数据
            result = self._get_search_index(city_code, keywords, start_date, end_date)
            if not result:
                log.warning(f"获取数据失败，跳过当前任务: {city_code}, {start_date}-{end_date}, 关键词数量: {len(keywords)}")
                
                # 构造空结果
                if not is_batch:
                    # 单关键词模式
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
                else:
                    # 批量模式，为每个关键词构造空结果
                    empty_daily_data = []
                    empty_stats_records = []
                    
                    for keyword in keywords:
                        task_key = f"{keyword}_{city_code}_{start_date}_{end_date}"
                        
                        empty_daily_data.append({
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
                        })
                        
                        empty_stats_records.append({
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
                        })
                    
                    # 返回所有关键词的任务键和空结果
                    return [f"{kw}_{city_code}_{start_date}_{end_date}" for kw in keywords], empty_daily_data, empty_stats_records
        except NoCookieAvailableError:
            # 向上层抛出异常，通知主线程暂停任务
            raise
        except Exception as e:
            log.error(f"处理任务时出错: {e}")
            # 构造空结果，与上面相同
            if not is_batch:
                # 单关键词模式
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
            else:
                # 批量模式，为每个关键词构造空结果
                empty_daily_data = []
                empty_stats_records = []
                
                for keyword in keywords:
                    empty_daily_data.append({
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
                    })
                    
                    empty_stats_records.append({
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
                    })
                
                # 返回所有关键词的任务键和空结果
                return [f"{kw}_{city_code}_{start_date}_{end_date}" for kw in keywords], empty_daily_data, empty_stats_records
        
        data, cookie = result
        
        # 处理数据
        if not is_batch:
            # 单关键词处理
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
        else:
            # 批量处理多个关键词
            daily_data_list, stats_records_list = self._process_multi_search_index_data(
                data, cookie, keywords, city_code, city_name, start_date, end_date
            )
            
            # 如果处理结果为空，构造空结果
            if not daily_data_list or not stats_records_list:
                log.warning(f"批量处理数据失败，构造空结果: {city_code}, {start_date}-{end_date}, 关键词数量: {len(keywords)}")
                log.warning(f"data: {data}")
                log.warning(f"daily_data_list: {daily_data_list}")
                log.warning(f"stats_records_list: {stats_records_list}")
                
                empty_daily_data = []
                empty_stats_records = []
                
                for keyword in keywords:
                    empty_daily_data.append({
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
                    })
                    
                    empty_stats_records.append({
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
                    })
                
                # 返回所有关键词的任务键和空结果
                return [f"{kw}_{city_code}_{start_date}_{end_date}" for kw in keywords], empty_daily_data, empty_stats_records
            
            # 返回所有关键词的任务键和处理结果
            return [f"{kw}_{city_code}_{start_date}_{end_date}" for kw in keywords], daily_data_list, stats_records_list

    
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
                                # 判断是单个任务还是批量任务
                                if isinstance(result[0], list):
                                    # 批量任务
                                    task_keys, daily_data, stats_records = result
                                    
                                    # 确保 daily_data 和 stats_records 不为 None
                                    if daily_data is not None and stats_records is not None:
                                        # 添加到本地缓存
                                        local_data_cache.extend(daily_data)
                                        local_stats_cache.extend(stats_records)
                                        
                                        # 更新全局任务状态
                                        with self.task_lock:
                                            for task_key in task_keys:
                                                self.completed_keywords.add(task_key)
                                                self.completed_tasks += 1
                                            # 每完成10个任务保存一次检查点
                                            if self.completed_tasks % 10 == 0:
                                                self._save_global_checkpoint()
                                else:
                                    # 单个任务
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
                                if len(local_data_cache) >= 200:
                                    with self.save_lock:
                                        self._save_data_to_file(local_data_cache, local_stats_cache)
                                    local_data_cache = []
                                    local_stats_cache = []
                                    
                                    # 计算当前进度百分比
                                    current_progress_percent = ((self.completed_tasks / self.total_tasks) * 100)
                                    # log.info(f"当前进度: {current_progress_percent}%, 上次进度: {last_progress_percent}%")
                                    # 每完成0.05%的任务更新一次数据库进度
                                    if current_progress_percent >= last_progress_percent + 0.05:
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
                                                
                                                # 推送 WebSocket 更新
                                                try:
                                                    from utils.websocket_manager import emit_task_update
                                                    emit_task_update(self.task_id, {
                                                        'progress': min(current_progress_percent, 100),
                                                        'completed_items': self.completed_tasks,
                                                        'total_items': self.total_tasks,
                                                        'status': 'running'
                                                    })
                                                except Exception as ws_error:
                                                    log.debug(f"推送 WebSocket 更新失败: {ws_error}")
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
                                    
                                    # 每完成2000条任务更新一次ab_sr cookie
                                    if self.completed_tasks - last_ab_sr_update_task_count >= 120000:
                                        log.info(f"已完成{self.completed_tasks}条任务，开始更新ab_sr cookie...")
                                        self._update_ab_sr_cookies()
                                        last_ab_sr_update_task_count = self.completed_tasks
                                    
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
                    log.error(f"任务执行过程中出错: {e}")
                    # 如果是NoCookieAvailableError，更新任务状态为暂停
                    if isinstance(e, NoCookieAvailableError):
                        log.warning("没有可用的Cookie，任务将被暂停")
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
                        log.error("任务因非Cookie问题失败")
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
    def _save_data_to_file(self, data_cache, stats_cache, status=None):
        """保存本地缓存数据到文件并更新数据库统计"""
        try:
            data_count = 0
            stats_count = 0
            
            if data_cache:
                # 保存日度/周度数据
                daily_df = pd.DataFrame(data_cache)
                daily_path = os.path.join(self.output_path, f"search_index_{self.task_id}_daily_data.csv")
                
                # 记录实际保存的数据条数
                data_count = len(daily_df)
                
                # 判断文件是否存在，决定是否写入表头
                file_exists = os.path.isfile(daily_path)
                daily_df.to_csv(daily_path, mode='a', header=not file_exists, index=False, encoding='utf-8-sig')
                
                # 维护总保存计数器（推荐方式）
                if not hasattr(self, '_total_saved_count'):
                    self._total_saved_count = 0
                self._total_saved_count += data_count
                
                # 显示进度信息
                progress = 100.0 * self.completed_tasks / self.total_tasks if self.total_tasks > 0 else 0
                log.info(f"进度: [{self.completed_tasks}/{self.total_tasks}] {progress:.2f}% - 已保存{data_count}条数据记录")
                
            if stats_cache:
                # 保存统计数据
                stats_df = pd.DataFrame(stats_cache)
                stats_path = os.path.join(self.output_path, f"search_index_{self.task_id}_stats_data.csv")
                
                # 记录实际保存的数据条数
                stats_count = len(stats_df)
                
                # 判断文件是否存在，决定是否写入表头
                file_exists = os.path.isfile(stats_path)
                stats_df.to_csv(stats_path, mode='a', header=not file_exists, index=False, encoding='utf-8-sig')
            
            # 同时保存检查点，确保数据一致性
            if data_cache or stats_cache:
                self._save_global_checkpoint()
            
            # 更新数据库统计数据 - 如果是任务完成时的保存或者有数据保存时
            if (status == "completed" or data_count > 0) and hasattr(self, 'task_id'):
                try:
                    # 计算该任务的总爬取数据条数
                    total_crawled = 0
                    
                    if status == "completed":
                        # 任务完成时，使用更快的方式统计总行数
                        daily_path = os.path.join(self.output_path, f"search_index_{self.task_id}_daily_data.csv")
                        if os.path.exists(daily_path):
                            # 方式1：使用缓存的计数器（推荐）
                            if hasattr(self, '_total_saved_count'):
                                total_crawled = self._total_saved_count
                            else:
                                # 方式2：使用更快的行数统计方法
                                total_crawled = self._fast_count_csv_rows(daily_path)
                    else:
                        # 定期保存时，只使用本次新增的数据量
                        total_crawled = data_count
                    
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
                        
                        # 计算新的累计爬取数据条数
                        if status == "completed":
                            # 任务完成时，需要重新计算总数据量
                            new_total_crawled = current_total_crawled + total_crawled
                        else:
                            # 定期保存时，只累加新增数据量
                            new_total_crawled = current_total_crawled + total_crawled
                        
                        # 更新统计记录
                        update_query = """
                            UPDATE spider_statistics
                            SET total_crawled_items = %s,
                                update_time = %s
                            WHERE id = %s
                        """
                        mysql.execute_query(update_query, (new_total_crawled, datetime.now(), stats['id']))
                        
                        # log.info(f"更新累计爬取数据条数: {current_total_crawled} -> {new_total_crawled} (新增: {total_crawled})")
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
                    log.error(f"在_save_data_to_file中更新统计数据失败: {e}")
                    log.error(traceback.format_exc())
                    
        except Exception as e:
            log.error(f"保存数据到文件时出错: {e}")
            log.error(traceback.format_exc())

    def _fast_count_csv_rows(self, filepath):
        """快速统计CSV文件行数（不包含表头）"""
        try:
            # 方式1：使用缓冲区读取，适合大文件
            with open(filepath, 'rb') as f:
                # 跳过可能的BOM
                if f.read(3) != b'\xef\xbb\xbf':
                    f.seek(0)
                
                # 统计换行符数量
                lines = 0
                buffer_size = 8192
                while True:
                    buffer = f.read(buffer_size)
                    if not buffer:
                        break
                    lines += buffer.count(b'\n')
                
                # 减去表头行
                return max(0, lines - 1) if lines > 0 else 0
                
        except Exception as e:
            log.error(f"快速统计CSV行数失败: {e}")
            # 降级到传统方式
            try:
                with open(filepath, 'r', encoding='utf-8-sig') as f:
                    return sum(1 for _ in f) - 1
            except Exception:
                return 0

        """初始化已保存数据计数器（用于任务重启时恢复计数）"""
        if not hasattr(self, '_total_saved_count'):
            daily_path = os.path.join(self.output_path, f"search_index_{self.task_id}_daily_data.csv")
            if os.path.exists(daily_path):
                self._total_saved_count = self._fast_count_csv_rows(daily_path)
            else:
                self._total_saved_count = 0
        """保存本地缓存数据到文件并更新数据库统计"""
        try:
            data_count = 0
            stats_count = 0
            
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
                
                # 记录实际保存的数据条数
                stats_count = len(stats_df)
                
                # 判断文件是否存在，决定是否写入表头
                file_exists = os.path.isfile(stats_path)
                stats_df.to_csv(stats_path, mode='a', header=not file_exists, index=False, encoding='utf-8-sig')
            
            # 同时保存检查点，确保数据一致性
            if data_cache or stats_cache:
                self._save_global_checkpoint()
            
            # 更新数据库统计数据 - 如果是任务完成时的保存或者有数据保存时
            if (status == "completed" or data_count > 0) and hasattr(self, 'task_id'):
                try:
                    # 计算该任务的总爬取数据条数
                    total_crawled = 0
                    
                    # 计算日度数据文件的行数
                    daily_path = os.path.join(self.output_path, f"search_index_{self.task_id}_daily_data.csv")
                    if os.path.exists(daily_path):
                        with open(daily_path, 'r', encoding='utf-8-sig') as f:
                            total_crawled = sum(1 for _ in f) - 1  # 减去表头行
                    
                    # 如果不是任务完成状态，只更新本次新增的数据量
                    if status != "completed":
                        total_crawled = data_count
                    
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
                        
                        # 计算新的累计爬取数据条数
                        if status == "completed":
                            # 任务完成时，需要重新计算总数据量
                            new_total_crawled = current_total_crawled + total_crawled
                        else:
                            # 定期保存时，只累加新增数据量
                            new_total_crawled = current_total_crawled + total_crawled
                        
                        # 更新统计记录
                        update_query = """
                            UPDATE spider_statistics
                            SET total_crawled_items = %s,
                                update_time = %s
                            WHERE id = %s
                        """
                        mysql.execute_query(update_query, (new_total_crawled, datetime.now(), stats['id']))
                        
                        # log.info(f"更新累计爬取数据条数: {current_total_crawled} -> {new_total_crawled} (新增: {total_crawled})")
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
                    log.error(f"在_save_data_to_file中更新统计数据失败: {e}")
                    log.error(traceback.format_exc())
                    
        except Exception as e:
            log.error(f"保存数据到文件时出错: {e}")
            log.error(traceback.format_exc())
# 创建爬虫实例
search_index_crawler = SearchIndexCrawler()

 