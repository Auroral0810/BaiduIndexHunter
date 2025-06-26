"""
并行爬虫模块，用于多线程爬取百度指数数据
"""
import os
import time
import json
import pandas as pd
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED
from datetime import datetime, timedelta
from utils.logger import log
from config.settings import SPIDER_CONFIG, OUTPUT_DIR
from spider.baidu_index_api import baidu_index_api
from cookie_manager.cookie_rotator import cookie_rotator
from db.redis_manager import redis_manager
from utils.city_manager import city_manager


class ParallelCrawler:
    """
    并行爬虫，支持多线程爬取百度指数数据
    """
    
    def __init__(self, max_workers=None, batch_size=10):
        """
        初始化并行爬虫
        :param max_workers: 最大工作线程数，默认为配置值或CPU核心数的2倍
        :param batch_size: 每个批次的关键词数量
        """
        self.max_workers = max_workers or SPIDER_CONFIG.get('max_workers', None)
        self.batch_size = batch_size
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.progress_lock = threading.Lock()
        self.progress_file = os.path.join('data', 'crawler_progress.json')
        self.progress = self._load_progress()
        self.data_batches_dir = os.path.join('data', 'data_batches')
        
        # 数据频率、数据源类型和数据类型
        self.data_frequency = 'week'  # 默认周度数据
        self.data_source_type = 'all'  # 默认所有终端
        self.data_type = 'all'  # 默认所有类型
        
        # 确保输出目录存在
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(self.data_batches_dir, exist_ok=True)
    
    def _load_progress(self):
        """加载爬取进度"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            log.error(f"加载爬取进度失败: {e}")
            return {}
    
    def _save_progress(self):
        """保存爬取进度"""
        try:
            with self.progress_lock:
                with open(self.progress_file, 'w', encoding='utf-8') as f:
                    json.dump(self.progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.error(f"保存爬取进度失败: {e}")
    
    def _update_progress(self, keyword, area, index_type, year, status):
        """
        更新爬取进度
        :param keyword: 关键词
        :param area: 地区代码
        :param index_type: 指数类型 (search/trend)
        :param year: 年份
        :param status: 状态 (success/failed)
        """
        with self.progress_lock:
            # 生成任务标识（新格式同时兼容旧格式）
            key = f"{keyword}_{area}_{year}"
            
            self.progress[key] = {
                'keyword': keyword,
                'area': area,
                'index_type': index_type,
                'year': year,
                'status': status,
                'timestamp': datetime.now().isoformat()
            }
    
    def _is_completed(self, keyword, area, index_type, year):
        """
        检查任务是否已完成
        :param keyword: 关键词
        :param area: 地区代码
        :param index_type: 指数类型
        :param year: 年份
        :return: 是否已完成且成功
        """
        # 生成任务标识（与进度文件中的格式一致）
        task_id = f"{keyword}_{area}_{year}"
        
        # 从进度文件中检查，只有status=success的任务才视为已完成
        if task_id in self.progress and self.progress[task_id]['status'] == 'success':
            # 检查index_type是否匹配
            if self.progress[task_id].get('index_type') == index_type:
                return True
        
        # 兼容旧格式的键（如果存在）
        old_task_id = f"{keyword}_{area}_{index_type}_{year}"
        if old_task_id in self.progress and self.progress[old_task_id]['status'] == 'success':
            return True
            
        return False
    
    def load_keywords(self, file_path):
        """
        从Excel文件加载关键词列表
        :param file_path: Excel文件路径
        :return: 关键词列表
        """
        try:
            df = pd.read_excel(file_path)
            if '关键词' in df.columns:
                keywords = df['关键词'].dropna().unique().tolist()
                # log.info(f"从 {file_path} 加载了 {len(keywords)} 个关键词")
                return keywords
            else:
                log.error(f"文件 {file_path} 中没有'关键词'列")
                return []
        except Exception as e:
            log.error(f"加载关键词文件失败: {e}")
            return []
    
    def create_tasks(self, keywords, areas=None, years=None, index_types=None):
        """
        创建爬取任务
        :param keywords: 关键词列表
        :param areas: 地区代码列表，默认为[0]（全国）
        :param years: 年份列表，默认为[当前年份]
        :param index_types: 指数类型列表，默认为['search']
        :return: 创建的任务数量
        """
        if not keywords:
            log.error("关键词列表为空")
            return 0
            
        # 设置默认值
        areas = areas or [0]
        current_year = datetime.now().year
        years = years or [current_year]
        index_types = index_types or ['search']
    
        
        # 理论上的总任务数
        total_tasks = len(keywords) * len(areas) * len(years) * len(index_types)
        
        # 清空任务队列
        while not self.task_queue.empty():
            self.task_queue.get()
            
        # 创建任务
        task_count = 0
        skipped_count = 0
        for keyword in keywords:
            for area in areas:
                for year in years:
                    for index_type in index_types:
                        # 检查是否已完成
                        if self._is_completed(keyword, area, index_type, year):
                            # log.debug(f"任务已完成，跳过: {keyword} - 地区:{area} - 类型:{index_type} - 年份:{year}")
                            skipped_count += 1
                            continue
                            
                        # 创建任务
                        task = {
                            'keyword': keyword,
                            'area': area,
                            'year': year,
                            'index_type': index_type
                        }
                        self.task_queue.put(task)
                        task_count += 1
        
        # 打印跳过的任务数
        if skipped_count > 0:
            log.info(f"已跳过 {skipped_count} 个已成功完成的任务")
        
        return task_count
    
    def _worker(self, task):
        """工作线程函数"""
        keyword = task['keyword']
        area = task['area']
        index_type = task['index_type']
        year = task['year']
        
        log.info(f"开始爬取: {keyword} - 地区:{area} - 类型:{index_type} - 年份:{year}")
        
        # 计算日期范围
        if year == datetime.now().year:
            # 如果是当前年份，使用1月1日到当前日期
            start_date = f"{year}-01-01"
            end_date = datetime.now().strftime('%Y-%m-%d')
        else:
            # 否则使用整年
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"
        
        # 检查cookie是否可用，如果不可用则等待
        if not cookie_rotator.cookies_available_event.is_set():
            log.info(f"任务 {keyword}-{area}-{year} 等待Cookie可用...")
            # 等待cookie可用，最多等待30分钟
            if not cookie_rotator.wait_for_available_cookie(timeout=1800):
                log.error(f"任务 {keyword}-{area}-{year} 等待Cookie超时，任务失败")
                self.task_queue.task_done()
                return False
            log.info(f"Cookie已可用，继续执行任务: {keyword}-{area}-{year}")
        
        # 根据指数类型调用不同的API
        try:
            if index_type == 'search':
                df = baidu_index_api.get_search_index(
                    keyword=keyword, 
                    area=area, 
                    start_date=start_date, 
                    end_date=end_date, 
                    year=year,
                    data_frequency=self.data_frequency,
                    data_source_type=self.data_source_type,
                    data_type=self.data_type
                )
            elif index_type == 'trend':
                df = baidu_index_api.get_trend_index(
                    keyword=keyword, 
                    area=area,
                    start_date=start_date, 
                    end_date=end_date,
                    year=year,
                    data_frequency=self.data_frequency,
                    data_source_type=self.data_source_type,
                    data_type=self.data_type
                )
            else:
                log.error(f"未知的指数类型: {index_type}")
                df = None
            
            if df is not None and not df.empty:
                # 将结果放入结果队列
                self.result_queue.put({
                    'task': task,
                    'data': df,
                    'status': 'success'
                })
                self._update_progress(keyword, area, index_type, year, 'success')
            else:
                self.result_queue.put({
                    'task': task,
                    'data': None,
                    'status': 'failed'
                })
                self._update_progress(keyword, area, index_type, year, 'failed')
        
        except Exception as e:
            log.error(f"爬取失败: {keyword} - 地区:{area} - 类型:{index_type} - 年份:{year} - 错误:{e}")
            self.result_queue.put({
                'task': task,
                'data': None,
                'status': 'failed',
                'error': str(e)
            })
            self._update_progress(keyword, area, index_type, year, 'failed')
        
        finally:
            # 标记任务完成
            self.task_queue.task_done()
            
        return df is not None and not df.empty
    
    def _save_batch_results(self):
        """
        保存批次结果到Excel文件
        """
        try:
            # 如果结果为空，直接返回
            if self.result_queue.empty():
                return
            
            # 合并所有数据框
            dfs = []
            while not self.result_queue.empty():
                result = self.result_queue.get(block=False)
                if result['data'] is not None and not result['data'].empty:
                    dfs.append(result['data'])
            
            if not dfs:
                log.warning("没有有效数据")
                return
            
            combined_df = pd.concat(dfs, ignore_index=True)
            
            # 保存到Excel文件
            output_file = os.path.join(self.data_batches_dir, f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx")
            combined_df.to_excel(output_file, index=False)
            log.info(f"数据已保存到 {output_file}")
            
        except Exception as e:
            log.error(f"保存批次结果失败: {e}")
    
    def run(self):
        """运行爬虫"""
        # 检查任务队列是否为空
        if self.task_queue.empty():
            log.warning("任务队列为空，无需执行")
            return
            
        # 获取任务总数
        total_tasks = self.task_queue.qsize()
        log.info(f"开始执行 {total_tasks} 个爬取任务，最大线程数: {self.max_workers}")
        
        # 创建线程池
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            futures = []
            worker_tasks = {}  # 记录每个线程的任务分配情况
            tasks_list = []    # 保存所有任务，以便在cookie被锁定后重新提交
            
            # 从队列中获取所有任务
            for _ in range(total_tasks):
                task = self.task_queue.get()
                tasks_list.append(task)
            
            # 初始提交任务数量不超过max_workers
            initial_submit_count = min(self.max_workers, len(tasks_list))
            for i in range(initial_submit_count):
                task = tasks_list[i]
                future = executor.submit(self._worker, task)
                futures.append(future)
                
                # 记录线程任务
                worker_id = f"Worker-{i+1}"
                worker_tasks[worker_id] = {
                    'task': task,
                    'status': 'running',
                    'completed': False
                }
            
            # 进度统计变量
            completed = 0
            success = 0
            failure = 0
            next_task_index = initial_submit_count  # 下一个要提交的任务索引
            start_time = time.time()
            last_progress_time = start_time
            last_detailed_log_time = start_time  # 上次详细日志时间
            
            # 记录cookie锁定状态
            cookie_blocked_time = None
            active_futures = set(futures)  # 当前活跃的future集合
            
            # 处理完成的任务
            while active_futures:
                # 检查是否所有cookie都被锁定
                cookie_status = cookie_rotator.get_status()
                all_blocked = cookie_status['available'] == 0 and cookie_status['total'] > 0
                
                if all_blocked:
                    if cookie_blocked_time is None:
                        cookie_blocked_time = time.time()
                        log.warning("所有Cookie被锁定，暂停任务提交，等待Cookie解锁...")
                        
                        # 获取当前正在运行的任务数
                        running_tasks = sum(1 for worker_info in worker_tasks.values() 
                                          if not worker_info['completed'] and worker_info['status'] == 'running')
                        log.info(f"当前有 {running_tasks} 个任务正在运行，这些任务将等待Cookie解锁后继续")
                else:
                    # 如果之前被锁定，现在解锁了
                    if cookie_blocked_time is not None:
                        blocked_duration = time.time() - cookie_blocked_time
                        log.info(f"Cookie已解锁，恢复任务提交。锁定持续了 {blocked_duration / 60:.2f} 分钟")
                        cookie_blocked_time = None
                
                # 等待任意一个future完成
                done, not_done = wait(active_futures, timeout=5, return_when=FIRST_COMPLETED)
                
                # 处理完成的future
                for future in done:
                    active_futures.remove(future)
                    completed += 1
                    result = future.result()
                    if result:
                        success += 1
                    else:
                        failure += 1
                    
                    # 更新对应的worker状态
                    for worker_id, task_info in worker_tasks.items():
                        if not task_info['completed'] and task_info['status'] == 'running':
                            task_info['completed'] = True
                            task_info['status'] = 'success' if result else 'failed'
                            break
                    
                    # 如果cookie没有被锁定，并且还有未提交的任务，提交下一个任务
                    if cookie_blocked_time is None and next_task_index < len(tasks_list):
                        task = tasks_list[next_task_index]
                        future = executor.submit(self._worker, task)
                        active_futures.add(future)
                        
                        # 记录线程任务
                        worker_id = f"Worker-{next_task_index+1}"
                        worker_tasks[worker_id] = {
                            'task': task,
                            'status': 'running',
                            'completed': False
                        }
                        
                        next_task_index += 1
                
                # 计算进度
                progress = completed / total_tasks * 100
                
                # 每30秒或进度达到整数5%时输出进度
                current_time = time.time()
                if (current_time - last_progress_time >= 30) or (int(progress) % 5 == 0 and int(progress) > 0):
                    elapsed_seconds = current_time - start_time
                    elapsed_minutes = elapsed_seconds / 60
                    
                    # 计算速度和预估剩余时间
                    speed = completed / elapsed_minutes if elapsed_minutes > 0 else 0
                    remaining_tasks = total_tasks - completed
                    remaining_minutes = remaining_tasks / speed if speed > 0 else 0
                    
                    # 获取可用Cookie数量
                    available_cookies = cookie_status['available']
                    total_cookies = cookie_status['total']
                    
                    # 计算当前活跃线程数
                    active_threads = len(active_futures)
                    
                    # 输出进度信息
                    log.info(f"进度: {progress:.2f}% ({completed}/{total_tasks}), "
                             f"成功: {success}, 失败: {failure}, "
                             f"速度: {speed:.2f} 任务/分钟, "
                             f"已用时: {int(elapsed_minutes)}分钟, "
                             f"预计剩余: {int(remaining_minutes)}分钟, "
                             f"可用Cookie: {available_cookies}/{total_cookies}, "
                             f"活跃线程: {active_threads}/{self.max_workers}")
                    
                    # 绘制进度条
                    progress_bar_width = 50
                    filled_width = int(progress_bar_width * progress / 100)
                    bar = '█' * filled_width + '░' * (progress_bar_width - filled_width)
                    log.info(f"[{bar}] {progress:.1f}%")
                    
                    # 每5分钟输出一次详细的线程任务分配情况
                    if current_time - last_detailed_log_time >= 300:
                        log.info("===== 线程任务分配情况 =====")
                        running_count = 0
                        for worker_id, task_info in worker_tasks.items():
                            if not task_info['completed']:
                                running_count += 1
                                task = task_info['task']
                                log.info(f"{worker_id}: 正在爬取 {task['keyword']} - 地区:{task['area']} - 类型:{task['index_type']} - 年份:{task['year']}")
                        
                        log.info(f"当前运行中的线程数: {running_count}")
                        last_detailed_log_time = current_time
                    
                    # 更新上次进度时间
                    last_progress_time = current_time
        
        # 保存最后一批数据
        self._save_batch_results()
        
        # 最终统计
        elapsed_seconds = time.time() - start_time
        elapsed_minutes = elapsed_seconds / 60
        log.info(f"爬取完成，成功: {success}, 失败: {failure}, 总用时: {int(elapsed_minutes)}分钟")
    
    def merge_batch_results(self):
        """
        合并所有批次结果
        """
        try:
            # 获取所有批次文件
            batch_files = [f for f in os.listdir(self.data_batches_dir) if f.startswith('batch_') and f.endswith('.xlsx')]
            
            if not batch_files:
                log.warning("没有找到批次结果文件")
                return
            
            log.info(f"开始合并 {len(batch_files)} 个批次结果文件")
            
            # 读取所有批次文件
            dfs = []
            for file in batch_files:
                try:
                    file_path = os.path.join(self.data_batches_dir, file)
                    df = pd.read_excel(file_path)
                    dfs.append(df)
                    log.info(f"已读取: {file}")
                except Exception as e:
                    log.error(f"读取 {file} 失败: {e}")
            
            if not dfs:
                log.warning("没有成功读取任何批次数据")
                return
            
            # 合并所有数据框
            combined_df = pd.concat(dfs, ignore_index=True)
            
            # 创建输出目录
            merged_dir = os.path.join(OUTPUT_DIR, 'merged_results')
            os.makedirs(merged_dir, exist_ok=True)
            
            # 按照关键词、地区、日期排序
            combined_df = combined_df.sort_values(by=['keyword', 'area_code', 'date'])
            
            # 保存合并后的数据
            output_file = os.path.join(merged_dir, f"百度指数数据_{datetime.now().strftime('%Y%m%d')}.xlsx")
            combined_df.to_excel(output_file, index=False)
            log.info(f"合并后的数据已保存到 {output_file}")
            
            # 生成统计信息
            self._generate_statistics(combined_df, merged_dir)
            
        except Exception as e:
            log.error(f"合并批次结果失败: {e}")
    
    def _generate_statistics(self, df, output_dir):
        """
        生成统计信息
        :param df: 合并后的DataFrame
        :param output_dir: 输出目录
        """
        try:
            # 统计关键词数量
            keywords = df['keyword'].unique()
            keyword_count = len(keywords)
            
            # 统计地区数量
            areas = df['area_code'].unique()
            area_count = len(areas)
            
            # 创建统计信息DataFrame
            stats_data = []
            
            # 按关键词统计
            for keyword in keywords:
                keyword_df = df[df['keyword'] == keyword]
                keyword_areas = keyword_df['area_code'].unique()
                keyword_area_count = len(keyword_areas)
                
                # 统计每个关键词的数据条数
                stats_data.append({
                    '关键词': keyword,
                    '地区数量': keyword_area_count,
                    '数据条数': len(keyword_df)
                })
            
            # 创建统计信息DataFrame并排序
            stats_df = pd.DataFrame(stats_data)
            stats_df = stats_df.sort_values(by=['关键词'])
            
            # 保存统计信息
            stats_file = os.path.join(output_dir, "统计信息.xlsx")
            stats_df.to_excel(stats_file, index=False)
            log.info(f"统计信息已保存到 {stats_file}")
            
            # 输出总体统计信息
            log.info(f"总关键词数量: {keyword_count}")
            log.info(f"总地区数量: {area_count}")
            log.info(f"总数据条数: {len(df)}")
            
        except Exception as e:
            log.error(f"生成统计信息失败: {e}")


# 创建并行爬虫单例
parallel_crawler = ParallelCrawler() 