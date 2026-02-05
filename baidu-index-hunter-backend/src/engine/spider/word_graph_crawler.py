"""
需求图谱爬虫（关键词关联关系）
"""
import pandas as pd
import requests
import json
import time
import os
import pickle
import signal
import atexit
from datetime import datetime
import threading
import sys
import os
import json
import traceback
from datetime import datetime, timedelta
from src.core.logger import log
from src.utils.rate_limiter import rate_limiter
from src.utils.decorators import retry
from src.engine.crypto.cipher_generator import cipher_text_generator
from src.services.cookie_rotator import cookie_rotator
from src.core.config import BAIDU_INDEX_API, OUTPUT_DIR
from src.services.processor_service import data_processor
from fake_useragent import UserAgent
from src.data.repositories.mysql_manager import MySQLManager


class WordGraphCrawler:
    """需求图谱爬虫，负责获取百度指数的需求图谱数据"""
    
    def __init__(self):
        """初始化需求图谱爬虫"""
        self.word_graph_url = BAIDU_INDEX_API['word_graph_url']
        self.referer = BAIDU_INDEX_API['referer']
        self.ua = UserAgent()
        self.task_id = None
        self.checkpoint_dir = os.path.join(OUTPUT_DIR, 'checkpoints')
        self.output_dir = os.path.join(OUTPUT_DIR, 'word_graph')
        
        # 创建必要的目录
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 初始化任务状态
        self.task_status = {}
        self.lock = threading.RLock()
        
        # 初始化数据缓存
        self.data_cache = []
        self.data_cache_size = 100  # 每收集100条数据就保存一次
        
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
        self._save_on_exit()
        sys.exit(0)
    
    def _save_on_exit(self):
        """在程序退出时保存数据和检查点"""
        log.info("程序即将退出，保存数据和检查点...")
        # 保存数据缓存
        self._save_data_cache(force=True)
        # 保存当前任务状态作为检查点
        task_id = self._get_current_task_id()
        if task_id:
            self._save_global_checkpoint(task_id)
    
    def _save_data_cache(self, force=False, status=None):
        """
        保存数据缓存到CSV文件
        :param force: 是否强制保存，即使缓存未达到阈值
        :param status: 任务状态，如果是"completed"则更新统计数据
        :return: 是否保存成功
        """
        with self.lock:
            # 如果缓存为空，不保存
            if not self.data_cache:
                return False
            
            # 如果缓存未达到阈值且非强制保存，不保存
            if len(self.data_cache) < self.data_cache_size and not force:
                return False
            
            # 获取当前任务ID
            task_id = self._get_current_task_id()
            if not task_id:
                log.warning("无法获取当前任务ID，使用时间戳作为文件名")
                task_id = datetime.now().strftime('%Y%m%d%H%M%S')
            
            # 创建DataFrame
            df = pd.DataFrame(self.data_cache)
            
            # 构建输出文件路径
            output_path = os.path.join(self.output_dir, task_id,f"word_graph_{task_id}.csv")
            
            # 保存数据
            try:
                if os.path.exists(output_path):
                    # 追加到现有文件
                    data_processor.append_to_csv(df, output_path)
                else:
                    # 创建新文件
                    data_processor.save_to_csv(df, output_path)
                
                log.info(f"成功保存 {len(self.data_cache)} 条数据到 {output_path}")
                
                # 更新任务状态中的输出文件路径
                if task_id in self.task_status:
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
                            mysql.execute_query(insert_query, (stat_date, task_type, total_crawled,  now))
                            
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
        return os.path.join(self.checkpoint_dir, f"word_graph_checkpoint_{task_id}.pkl")
    
    def _save_global_checkpoint(self, task_id):
        """
        保存全局检查点
        :param task_id: 任务ID
        """
        checkpoint_path = self._get_checkpoint_path(task_id)
        try:
            with self.lock:
                with open(checkpoint_path, 'wb') as f:
                    pickle.dump(self.task_status[task_id], f)
            log.info(f"已保存全局检查点: {checkpoint_path}")
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
        return os.path.join(self.output_dir, f"word_graph_{task_id}.{file_type}")
    
    def _get_current_task_id(self):
        """
        获取当前正在执行的任务ID
        :return: 任务ID，如果没有当前任务则返回None
        """
        # with self.lock:
        #     # 查找状态为'running'的任务
        #     for task_id, status in self.task_status.items():
        #         if status.get('status') == 'running':
        #             return task_id
        return self.task_id
    
    @retry(max_retries=2)
    def get_word_graph(self, keyword, datelist):
        """
        获取需求图谱数据
        :param keyword: 关键词
        :param datelist: 日期，格式为YYYYMMDD
        :return: 需求图谱数据字典或None（请求失败）
        """
        try:
            # 获取一个可用的cookie
            account_id, cookie_dict = cookie_rotator.get_cookie()
            if not cookie_dict:
                log.warning(f"无法获取可用Cookie进行请求 [{keyword}, {datelist}]，所有Cookie可能都被锁定")
                # 等待有可用的cookie (最多等待30秒)
                if cookie_rotator.wait_for_available_cookie(timeout=30):
                    log.info(f"检测到有可用Cookie，重试获取 [{keyword}, {datelist}]")
                    # 重新尝试获取cookie
                    account_id, cookie_dict = cookie_rotator.get_cookie()
                    if not cookie_dict:
                        log.error(f"尽管收到可用Cookie通知，但仍无法获取Cookie，放弃请求 [{keyword}, {datelist}]")
                        return None
                else:
                    log.error(f"等待可用Cookie超时，放弃请求 [{keyword}, {datelist}]")
                    return None
            
            # 构建请求URL
            url = f'{self.word_graph_url}?wordlist[]={keyword}&datelist={datelist}'
            
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
            log.info(f"请求需求图谱: {keyword}, 日期: {datelist}")
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
                        log.info(f"检测到有其他可用Cookie，重试获取 [{keyword}, {datelist}]")
                        # 递归调用自身重试
                        return self.get_word_graph(keyword, datelist)
                else:
                    # 其他错误，临时锁定cookie
                    cookie_rotator.report_cookie_status(account_id, False)
                
                return None
            
            # 如果请求成功，标记cookie为有效
            cookie_rotator.report_cookie_status(account_id, True)
            
            log.info(f"成功获取 {keyword} 在 {datelist} 的需求图谱数据")
            return result
            
        except Exception as e:
            log.error(f"获取需求图谱数据失败: {e}")
            # 如果是因为cookie问题，将其标记为无效
            if account_id:
                cookie_rotator.report_cookie_status(account_id, False)
            return None
    
    def crawl(self, task_id, keywords, datelists=None, start_date=None, end_date=None, output_format='csv', resume=True, checkpoint_task_id=None):
        """
        爬取多个关键词和日期的需求图谱数据
        :param task_id: 任务ID，如果为None则自动生成
        :param keywords: 关键词列表
        :param datelists: 日期列表（兼容旧方式）
        :param start_date: 开始日期 YYYYMMDD
        :param end_date: 结束日期 YYYYMMDD
        :param output_format: 输出格式
        :param resume: 是否恢复
        :param checkpoint_task_id: 检查点ID
        :return: Success
        """
        # 确保输入是列表
        if isinstance(keywords, str):
            keywords = [keywords]
        
        # 构造日期列表 (Logic from test.py)
        if start_date and end_date:
            try:
                s_date = datetime.strptime(start_date, "%Y%m%d")
                e_date = datetime.strptime(end_date, "%Y%m%d")
                
                datelists = []
                current_date = s_date
                while current_date <= e_date:
                    datelists.append(current_date.strftime("%Y%m%d"))
                    # Weekly step
                    current_date += timedelta(days=7)
            except Exception as e:
                log.error(f"日期解析失败: {e}")
                datelists = []
        elif not datelists:
             datelists = []

        if isinstance(datelists, str):
            datelists = [datelists]
        
        # 确定任务ID
        if task_id is None:
            task_id = datetime.now().strftime('%Y%m%d%H%M%S')
        self.task_id = task_id
        log.info(f"开始爬取 {len(keywords)} 个关键词在 {len(datelists)} 个日期的需求图谱数据，任务ID: {task_id}")
        
        # 初始化任务状态
        with self.lock:
            # 检查是否有检查点数据
            checkpoint_status = None
            if resume:
                checkpoint_status = self._load_global_checkpoint(checkpoint_task_id)
            
            if checkpoint_status:
                log.info(f"从检查点恢复任务: {checkpoint_task_id}")
                self.task_status[task_id] = checkpoint_status
                
                # 检查数据文件是否存在
                output_file = checkpoint_status.get('output_file')
                if output_file and os.path.exists(output_file):
                    log.info(f"找到已存在的数据文件: {output_file}")
                else:
                    log.warning(f"未找到数据文件，将创建新文件")
                    self.task_status[task_id]['output_file'] = self._get_output_path(task_id, output_format)
            else:
                # 创建新任务状态
                log.info(f"创建新任务: {task_id}")
                self.task_status[task_id] = {
                    'task_id': task_id,
                    'status': 'running',
                    'total': len(keywords) * len(datelists),
                    'completed': 0,
                    'failed': 0,
                    'progress': 0,
                    'start_time': datetime.now(),
                    'last_update_time': datetime.now(),
                    'keywords': keywords,
                    'datelists': datelists,
                    'output_format': output_format,
                    'output_file': self._get_output_path(task_id, output_format),
                    'results': {},  # 存储已完成任务的状态，格式：{(keyword, datelist): {'status': 'success|failed', ...}}
                    'checkpoint_time': datetime.now()
                }
                
                # 保存初始检查点
                self._save_global_checkpoint(task_id)
        
        # 计算总任务数和已完成任务数
        total_tasks = len(keywords) * len(datelists)
        completed_tasks = 0
        
        # 如果有检查点，计算已完成的任务数
        if checkpoint_status:
            completed_tasks = checkpoint_status.get('completed', 0)
            log.info(f"从检查点恢复：总任务数 {total_tasks}，已完成 {completed_tasks}，进度 {completed_tasks/total_tasks*100:.2f}%")
        
        # 遍历关键词和日期
        for keyword in keywords:
            for datelist in datelists:
                # 检查任务是否已完成
                task_key = (keyword, datelist)
                if task_key in self.task_status[task_id]['results'] and self.task_status[task_id]['results'][task_key].get('status') == 'success':
                    log.info(f"跳过已完成的任务: {keyword}, {datelist}")
                    continue
                
                # 获取需求图谱数据
                result = None
                max_retries = 2  # 最大重试次数
                retry_count = 0
                
                while result is None and retry_count < max_retries:
                    result = self.get_word_graph(keyword, datelist)
                    
                    if result is None:
                        retry_count += 1
                        # 检查是否所有Cookie都被锁定
                        cookie_status = cookie_rotator.get_status()
                        all_cookies_blocked = cookie_status.get('available', 0) == 0 and cookie_status.get('blocked', 0) > 0
                        
                        if all_cookies_blocked:
                            log.warning(f"所有Cookie都被锁定，等待可用Cookie后重试 (尝试 {retry_count}/{max_retries})")
                            # 等待Cookie可用，最多等待60秒
                            if cookie_rotator.wait_for_available_cookie(timeout=60):
                                log.info(f"检测到有可用Cookie，重试获取 [{keyword}, {datelist}]")
                            else:
                                log.warning(f"等待可用Cookie超时，尝试继续重试 (尝试 {retry_count}/{max_retries})")
                        else:
                            # 如果不是因为所有Cookie都被锁定，则短暂等待后重试
                            wait_time = retry_count * 5  # 逐渐增加等待时间
                            log.info(f"请求失败，等待 {wait_time} 秒后重试 (尝试 {retry_count}/{max_retries})")
                            time.sleep(wait_time)
                
                # 处理结果
                if result:
                    # 处理数据
                    data_records = []
                    
                    # 获取数据
                    api_data = result['data']
                    if not isinstance(api_data, dict):
                        log.error(f"API返回data字段不是字典，实际类型: {type(api_data)}, 内容: {api_data}")
                        # 标记任务失败
                        with self.lock:
                            self.task_status[task_id]['failed'] += 1
                            self.task_status[task_id]['last_update_time'] = datetime.now()
                            self.task_status[task_id]['results'][task_key] = {
                                'status': 'failed',
                                'error': f"API返回data字段不是字典，内容: {api_data}",
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                        continue  # 跳过本次
                    period = api_data.get('period', '')
                    
                    # 处理每个关键词的数据
                    for word_item in api_data.get('wordlist', []):
                        item_keyword = word_item.get('keyword', keyword)
                        word_graph = word_item.get('wordGraph', [])
                        
                        # 如果没有相关词数据，添加一个空行
                        if not word_graph:
                            data_records.append({
                                '关键词': item_keyword,
                                '相关词': '',
                                '搜索量': 0,
                                '变化率': 0,
                                '相关度': 0,
                                '数据周期': period,
                                '日期': datelist,
                                '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            continue
                        
                        # 处理每个相关词
                        for item in word_graph:
                            related_word = item.get('word', '')
                            pv = item.get('pv', 0)
                            ratio = item.get('ratio', 0)
                            sim = item.get('sim', 0)
                            
                            data_records.append({
                                '关键词': item_keyword,
                                '相关词': related_word,
                                '搜索量': pv,
                                '变化率': ratio,
                                '相关度': sim,
                                '数据周期': period,
                                '日期': datelist,
                                '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                    
                    # 将数据添加到缓存
                    with self.lock:
                        self.data_cache.extend(data_records)
                        
                        # 如果缓存达到阈值，保存数据
                        if len(self.data_cache) >= self.data_cache_size:
                            self._save_data_cache(force=True, status="running")
                    
                    # 更新任务状态
                    with self.lock:
                        self.task_status[task_id]['completed'] += 1
                        self.task_status[task_id]['progress'] = round(self.task_status[task_id]['completed'] / self.task_status[task_id]['total'] * 100, 2)
                        self.task_status[task_id]['last_update_time'] = datetime.now()
                        self.task_status[task_id]['results'][task_key] = {
                            'status': 'success',
                            'record_count': len(data_records),
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                    
                    # 定期保存检查点（每10个任务或2分钟保存一次）
                    with self.lock:
                        current_time = datetime.now()
                        time_since_checkpoint = (current_time - self.task_status[task_id]['checkpoint_time']).total_seconds()
                        if (self.task_status[task_id]['completed'] % 10 == 0) or (time_since_checkpoint > 120):
                            self._save_global_checkpoint(task_id)
                            self.task_status[task_id]['checkpoint_time'] = current_time
                    
                    log.info(f"成功爬取 {keyword} 在 {datelist} 的需求图谱数据，共 {len(data_records)} 条记录，"
                           f"总进度：{self.task_status[task_id]['progress']}%")
                else:
                    # 更新任务状态
                    with self.lock:
                        self.task_status[task_id]['failed'] += 1
                        self.task_status[task_id]['last_update_time'] = datetime.now()
                        self.task_status[task_id]['results'][task_key] = {
                            'status': 'failed',
                            'error': '请求失败或数据处理失败',
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                    
                    log.error(f"爬取 {keyword} 在 {datelist} 的需求图谱数据失败")
        
        # 保存剩余的数据缓存
        self._save_data_cache(force=True, status="completed")
        
        # 更新任务完成状态
        with self.lock:
            failed_count = self.task_status[task_id]['failed']
            total_count = self.task_status[task_id]['total']
            completed_count = self.task_status[task_id]['completed']
            
            self.task_status[task_id]['end_time'] = datetime.now()
            elapsed_time = (self.task_status[task_id]['end_time'] - self.task_status[task_id]['start_time']).total_seconds()
            success_rate = round(completed_count / total_count * 100, 2) if total_count > 0 else 0
            
            log.info(f"任务 {task_id} 完成: 总计 {total_count} 个任务，"
                   f"成功 {completed_count} 个，"
                   f"失败 {failed_count} 个，"
                   f"成功率 {success_rate}%，"
                   f"耗时 {elapsed_time:.2f} 秒")
            
            # 保存最终检查点
            self._save_global_checkpoint(task_id)
            
            # 根据失败数量更新数据库状态
            try:
                mysql = MySQLManager()
                now = datetime.now()
                
                if failed_count > 0:
                    # 有失败的任务，将整体任务标记为失败状态
                    fail_rate = (failed_count / total_count * 100) if total_count > 0 else 0
                    error_message = f"任务执行完成但有 {failed_count} 个子任务失败（失败率: {fail_rate:.2f}%），需要重试"
                    
                    self.task_status[task_id]['status'] = 'failed'
                    self.task_status[task_id]['error_message'] = error_message
                    
                    update_query = """
                        UPDATE spider_tasks 
                        SET progress = 100, completed_items = %s, failed_items = %s, 
                            status = 'failed', error_message = %s, update_time = %s, end_time = %s
                        WHERE task_id = %s
                    """
                    mysql.execute_query(update_query, (completed_count, failed_count, error_message, now, now, task_id))
                    
                    log.warning(f"任务完成但有失败项! 成功: {completed_count}, 失败: {failed_count}, 总计: {total_count}")
                    
                    # 推送 WebSocket 更新
                    try:
                        from src.services.websocket_service import emit_task_update
                        emit_task_update(task_id, {
                            'progress': 100,
                            'completed_items': completed_count,
                            'failed_items': failed_count,
                            'total_items': total_count,
                            'status': 'failed',
                            'error_message': error_message
                        })
                    except Exception as ws_error:
                        log.debug(f"推送 WebSocket 更新失败: {ws_error}")
                    
                    return False
                else:
                    # 全部成功完成
                    self.task_status[task_id]['status'] = 'completed'
                    
                    update_query = """
                        UPDATE spider_tasks 
                        SET progress = 100, completed_items = %s, failed_items = 0, 
                            status = 'completed', update_time = %s, end_time = %s
                        WHERE task_id = %s
                    """
                    mysql.execute_query(update_query, (completed_count, now, now, task_id))
                    
                    log.info(f"任务完成! 总共处理了 {completed_count}/{total_count} 个任务")
                    
                    # 推送 WebSocket 更新
                    try:
                        from src.services.websocket_service import emit_task_update
                        emit_task_update(task_id, {
                            'progress': 100,
                            'completed_items': completed_count,
                            'failed_items': 0,
                            'total_items': total_count,
                            'status': 'completed'
                        })
                    except Exception as ws_error:
                        log.debug(f"推送 WebSocket 更新失败: {ws_error}")
                    
                    return True
            except Exception as e:
                log.error(f"更新最终任务状态失败: {e}")
                return failed_count == 0
    
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
        datelists = checkpoint_status.get('datelists', [])
        output_format = checkpoint_status.get('output_format', 'csv')
        
        # 恢复任务
        return self.crawl(keywords, datelists, output_format=output_format, resume=True, task_id=task_id)
    
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
    
    def regenerate_data_file(self, task_id):
        """
        从检查点重新生成数据文件，即使任务已完成
        :param task_id: 任务ID
        :return: 是否成功重新生成
        """
        # 加载检查点
        checkpoint_status = self._load_global_checkpoint(task_id)
        if not checkpoint_status:
            log.error(f"无法重新生成数据文件，任务 {task_id} 的检查点不存在")
            return False
        
        log.info(f"从检查点 {task_id} 重新生成数据文件")
        
        # 获取任务参数
        output_format = checkpoint_status.get('output_format', 'csv')
        results = checkpoint_status.get('results', {})
        
        if not results:
            log.warning(f"任务 {task_id} 没有已完成的结果记录，无法重新生成数据文件")
            return False
        
        # 创建数据记录列表
        data_records = []
        
        # 遍历所有已完成的任务
        completed_count = 0
        for task_key, task_result in results.items():
            if task_result.get('status') == 'success':
                keyword, datelist = task_key
                
                # 重新获取数据
                log.info(f"重新获取 {keyword} 在 {datelist} 的需求图谱数据")
                result = self.get_word_graph(keyword, datelist)
                
                if result:
                    # 处理数据
                    api_data = result['data']
                    period = api_data.get('period', '')
                    
                    # 处理每个关键词的数据
                    for word_item in api_data.get('wordlist', []):
                        item_keyword = word_item.get('keyword', keyword)
                        word_graph = word_item.get('wordGraph', [])
                        
                        # 如果没有相关词数据，添加一个空行
                        if not word_graph:
                            data_records.append({
                                '关键词': item_keyword,
                                '相关词': '',
                                '搜索量': 0,
                                '变化率': 0,
                                '相关度': 0,
                                '数据周期': period,
                                '日期': datelist,
                                '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            continue
                        
                        # 处理每个相关词
                        for item in word_graph:
                            related_word = item.get('word', '')
                            pv = item.get('pv', 0)
                            ratio = item.get('ratio', 0)
                            sim = item.get('sim', 0)
                            
                            data_records.append({
                                '关键词': item_keyword,
                                '相关词': related_word,
                                '搜索量': pv,
                                '变化率': ratio,
                                '相关度': sim,
                                '数据周期': period,
                                '日期': datelist,
                                '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                    
                    completed_count += 1
                    log.info(f"成功重新获取 {keyword} 在 {datelist} 的需求图谱数据，共 {len(word_graph) if word_graph else 0} 条记录")
                else:
                    log.error(f"重新获取 {keyword} 在 {datelist} 的需求图谱数据失败")
        
        # 如果有数据，保存到文件
        if data_records:
            # 创建DataFrame
            df = pd.DataFrame(data_records)
            
            # 构建输出文件路径
            output_path = self._get_output_path(task_id, output_format)
            
            # 保存数据
            if output_format == 'csv':
                data_processor.save_to_csv(df, output_path)
            else:
                data_processor.save_to_excel(df, output_path)
            
            log.info(f"成功重新生成数据文件: {output_path}，共 {len(data_records)} 条记录，{completed_count} 个任务")
            
            # 更新任务状态中的输出文件路径
            with self.lock:
                if task_id in self.task_status:
                    self.task_status[task_id]['output_file'] = output_path
                    self._save_global_checkpoint(task_id)
            
            return True
        else:
            log.warning(f"没有数据可以保存，无法重新生成数据文件")
            return False


# 创建需求图谱爬虫单例
word_graph_crawler = WordGraphCrawler()

# if __name__ == "__main__":
#     # # 示例用法
#     # keywords = ["电脑", "手机", "平板"]
#     # datelists = ["20250501", "20250502"]
    
#     # # 爬取数据
#     # word_graph_crawler.crawl(keywords, datelists, output_format='csv', resume=True)
#     from spider.word_graph_crawler import word_graph_crawler

#     # 恢复指定任务ID的任务
#     task_id = "20250628001705"
#     word_graph_crawler.resume_task(task_id)

