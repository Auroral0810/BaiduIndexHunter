"""
任务管理模块
"""
import threading
import time
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.logger import log
from spider.baidu_index_api import baidu_index_api
from utils.data_processor import data_processor
from spider.progress_manager import progress_manager
from cookie_manager.cookie_rotator import cookie_rotator
from db.redis_manager import redis_manager
from db.mysql_manager import mysql_manager
from config.settings import SPIDER_CONFIG


class TaskManager:
    """
    任务管理器，负责管理爬取任务的执行
    """
    
    def __init__(self):
        self.max_workers = SPIDER_CONFIG.get('max_workers', 16)
        self.running = False
        self.stop_event = threading.Event()
        self.lock = threading.RLock()
        self.tasks = []
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.start_time = None
        self.results = []
        self.progress_summary_thread = None
        self.output_dir = Path(__file__).parent.parent / 'output'
        os.makedirs(self.output_dir, exist_ok=True)
        self.batch_dir = Path(__file__).parent.parent / 'data/data_batches'
        os.makedirs(self.batch_dir, exist_ok=True)
        self.batch_size = 100  # 每个批次的数据量
        self.current_batch = []
        self.batch_number = 0
    
    def create_tasks(self, keywords, areas, years, index_types=None):
        """
        创建爬取任务列表
        :param keywords: 关键词列表
        :param areas: 地区代码列表
        :param years: 年份列表
        :param index_types: 指数类型列表，可选值：['search', 'trend']，默认为['search']
        :return: 任务列表
        """
        # 默认指数类型为搜索指数
        if not index_types:
            index_types = ['search']
        
        tasks = []
        skipped = 0
        total = len(keywords) * len(areas) * len(years) * len(index_types)
        
        log.info(f"正在创建爬取任务，理论总数: {total}...")

        # 先重新加载进度文件，确保读取最新进度
        from spider.progress_manager import progress_manager
        progress_manager.load_progress()
        log.info(f"已从文件重新加载进度数据: {progress_manager.progress_file}")
        
        # 获取进度记录中成功状态的数量
        success_count = sum(1 for v in progress_manager.progress.values() if v.get('status') == 'success')
        log.info(f"进度文件中成功状态的任务数: {success_count}")
        
        # 获取进度文件中的一些键作为样本
        sample_keys = list(progress_manager.progress.keys())[:5]
        sample_values = [progress_manager.progress[k] for k in sample_keys[:5]]
        log.info(f"进度文件中的部分key示例: {sample_keys}")
        log.info(f"进度文件中的部分value示例: {sample_values}")

        # 检查每个任务是否已完成
        debug_samples = 0
        for keyword in keywords:
            for area in areas:
                for year in years:
                    for index_type in index_types:
                        # 如果需要调试，检查前几个任务的完成状态
                        if debug_samples < 5:
                            is_completed = progress_manager.is_completed(keyword, area, year, index_type)
                            key_with_type = f"{keyword}_{area}_{year}_{index_type}" 
                            key_without_type = f"{keyword}_{area}_{year}"
                            log.info(f"检查任务: {key_with_type}, 完成状态: {is_completed}")
                            log.info(f"  - 新格式key在进度中: {key_with_type in progress_manager.progress}")
                            log.info(f"  - 旧格式key在进度中: {key_without_type in progress_manager.progress}")
                            debug_samples += 1
                        
                        # 检查任务是否已完成
                        if progress_manager.is_completed(keyword, area, year, index_type):
                            skipped += 1
                            continue
                        
                        # 添加到任务列表
                        task = {
                            'keyword': keyword,
                            'area': area,
                            'year': year,
                            'index_type': index_type
                        }
                        tasks.append(task)
        
        log.info(f"任务创建完成，理论总任务: {total}，已完成跳过: {skipped}，待执行: {len(tasks)}")
        return tasks
    
    def start(self, keywords, areas, years, index_types=None):
        """
        启动爬取任务
        :param keywords: 关键词列表
        :param areas: 地区代码列表
        :param years: 年份列表
        :param index_types: 指数类型列表，可选值：['search', 'trend']，默认为['search']
        :return: 是否成功启动
        """
        if self.running:
            log.warning("任务管理器已在运行中")
            return False
        
        # 初始化状态
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.results = []
        self.current_batch = []
        self.batch_number = self._get_max_batch_number() + 1
        self.stop_event.clear()
        
        # 创建任务列表
        self.tasks = self.create_tasks(keywords, areas, years, index_types)
        total_tasks = len(self.tasks)
        
        if total_tasks == 0:
            log.info("没有需要爬取的任务，所有任务已完成")
            return True
        
        # 设置状态
        self.running = True
        self.start_time = time.time()
        
        # 启动进度汇总线程
        self.progress_summary_thread = threading.Thread(target=self._progress_summary_loop)
        self.progress_summary_thread.daemon = True
        self.progress_summary_thread.start()
        
        # 在新线程中启动爬取任务
        threading.Thread(target=self._execute_tasks).start()
        
        return True
    
    def stop(self):
        """停止爬取任务"""
        if not self.running:
            return
        
        log.info("正在停止爬取任务...")
        self.stop_event.set()
        
        # 等待进度汇总线程结束
        if self.progress_summary_thread and self.progress_summary_thread.is_alive():
            self.progress_summary_thread.join(timeout=2)
        
        # 保存剩余的批次数据
        if self.current_batch:
            self._save_current_batch()
        
        # 保存最终结果
        if self.results:
            self._save_results()
        
        self.running = False
        log.info("爬取任务已停止")
    
    def _execute_tasks(self):
        """执行爬取任务"""
        try:
            total_tasks = len(self.tasks)
            log.info(f"开始执行 {total_tasks} 个爬取任务")
            
            # 创建线程池
            available_workers = min(self.max_workers, total_tasks)
            
            # 检查可用cookie数量，最小值为1
            cookies_count = len(redis_manager.get_all_cached_cookie_ids() or [])
            cookies_count = max(1, cookies_count)
            
            # 根据可用cookie数量调整线程池大小
            workers = min(available_workers, cookies_count * 2)  # 每个cookie最多2个线程
            log.info(f"可用Cookie数量: {cookies_count}, 设置线程池大小为: {workers}")
            
            with ThreadPoolExecutor(max_workers=workers) as executor:
                # 提交所有任务
                future_to_task = {executor.submit(self._process_task, task): task for task in self.tasks}
                
                # 处理完成的任务
                for future in as_completed(future_to_task):
                    if self.stop_event.is_set():
                        log.info("收到停止信号，中断任务执行")
                        break
                    
                    # 检查是否所有Cookie都被锁定
                    cookie_status = cookie_rotator.get_status()
                    all_cookies_blocked = cookie_status.get('available', 0) == 0 and cookie_status.get('blocked', 0) > 0
                    
                    if all_cookies_blocked:
                        # 如果所有Cookie都被锁定，等待Cookie可用
                        wait_info = cookie_status.get('all_blocked_wait_info')
                        if wait_info:
                            remaining_mins = wait_info.get('remaining_minutes', 0)
                            if remaining_mins > 0:
                                log.info(f"所有Cookie都被锁定，任务执行暂停，等待Cookie冷却... 剩余约 {remaining_mins} 分钟")
                                # 等待Cookie可用，最多等待10秒
                                cookie_rotator.wait_for_available_cookie(timeout=10)
                    
                    task = future_to_task[future]
                    try:
                        result = future.result()
                        if result is not None and not result.empty:
                            self._add_to_batch(result)
                        self.completed_tasks += 1
                    except Exception as exc:
                        log.error(f"任务执行失败: {task}, 异常: {exc}")
                        self.failed_tasks += 1
            
            # 保存剩余的批次数据
            if self.current_batch:
                self._save_current_batch()
            
            # 保存最终结果
            self._save_results()
            
            log.info(f"爬取任务执行完成，共完成 {self.completed_tasks} 个任务，失败 {self.failed_tasks} 个任务")
        except Exception as e:
            log.error(f"执行爬取任务时发生错误: {e}")
        finally:
            self.running = False
    
    def _process_task(self, task):
        """
        处理单个爬取任务
        :param task: 任务信息字典
        :return: 处理结果
        """
        keyword = task['keyword']
        area = task['area']
        year = task['year']
        index_type = task.get('index_type', 'search')
        
        try:
            # 设置日期范围
            if year == datetime.now().year:
                start_date = f"{year}-01-01"
                # 2025年只到6月23日
                if year == 2025:
                    end_date = "2025-06-23"
                else:
                    end_date = datetime.now().strftime("%Y-%m-%d")
            else:
                start_date = f"{year}-01-01"
                # 2025年只到6月23日
                if year == 2025:
                    end_date = "2025-06-23"
                else:
                    end_date = f"{year}-12-31"
            
            # 根据指数类型调用不同的API
            if index_type == 'search':
                data = baidu_index_api.get_search_index(keyword, area, start_date, end_date)
                if data:
                    # 处理数据
                    df = data_processor.process_search_index_data(data, area, keyword, year)
                    
                    if not df.empty:
                        with self.lock:
                            self.results.append(df)
                        # 标记任务完成
                        progress_manager.mark_completed(keyword, area, year, index_type, status='success')
                        log.info(f"完成: {keyword}, 城市: {area}, 年份: {year}, 剩余: {len(self.tasks) - (self.completed_tasks + self.failed_tasks)}")
                        return df
                    else:
                        # 标记任务失败
                        progress_manager.mark_completed(keyword, area, year, index_type, status='failed')
                        return None
                else:
                    # 标记任务失败
                    progress_manager.mark_completed(keyword, area, year, index_type, status='failed')
                    return None
            
            elif index_type == 'trend':
                data = baidu_index_api.get_trend_index(keyword, area, start_date, end_date)
                if data:
                    # 处理数据
                    df = data_processor.process_trend_index_data(data, area, keyword, year)
                    
                    if not df.empty:
                        with self.lock:
                            self.results.append(df)
                        # 标记任务完成
                        progress_manager.mark_completed(keyword, area, year, index_type, status='success')
                        log.info(f"完成: {keyword}, 城市: {area}, 年份: {year}, 剩余: {len(self.tasks) - (self.completed_tasks + self.failed_tasks)}")
                        return df
                    else:
                        # 标记任务失败
                        progress_manager.mark_completed(keyword, area, year, index_type, status='failed')
                        return None
                else:
                    # 标记任务失败
                    progress_manager.mark_completed(keyword, area, year, index_type, status='failed')
                    return None
            
            else:
                # 标记任务失败
                progress_manager.mark_completed(keyword, area, year, index_type, status='failed')
                return None
        
        except Exception as e:
            # 标记任务失败
            progress_manager.mark_completed(keyword, area, year, index_type, status='failed')
            return None
    
    def _get_max_batch_number(self):
        """
        获取当前最大的批次号
        :return: 最大批次号
        """
        try:
            batch_files = list(self.batch_dir.glob('batch_*.xlsx'))
            if not batch_files:
                return 0
                
            # 从文件名中提取批次号
            batch_numbers = []
            for file_path in batch_files:
                try:
                    filename = file_path.name
                    # 文件名格式为 batch_NUMBER.xlsx
                    if filename.startswith('batch_') and filename.endswith('.xlsx'):
                        batch_number = int(filename[6:-5])  # 去掉 'batch_' 和 '.xlsx'
                        batch_numbers.append(batch_number)
                except (ValueError, IndexError):
                    continue
                    
            return max(batch_numbers) if batch_numbers else 0
        except Exception as e:
            log.error(f"获取最大批次号失败: {e}")
            return 0
    
    def _add_to_batch(self, df):
        """
        添加数据到当前批次
        :param df: 数据DataFrame
        """
        with self.lock:
            self.current_batch.append(df)
            
            # 检查是否达到批次大小
            if len(self.current_batch) >= self.batch_size:
                self._save_current_batch()
    
    def _save_current_batch(self):
        """保存当前批次数据"""
        if not self.current_batch:
            return
            
        try:
            # 合并当前批次的所有DataFrame
            batch_df = pd.concat(self.current_batch, ignore_index=True)
            
            # 生成批次文件名
            batch_file = self.batch_dir / f"batch_{self.batch_number}.xlsx"
            
            # 保存到Excel
            batch_df.to_excel(batch_file, index=False)
            log.info(f"已将 {len(batch_df)} 条结果保存到批次文件: {batch_file}")
            
            # 更新状态
            self.batch_number += 1
            self.current_batch = []
            
        except Exception as e:
            log.error(f"保存批次数据失败: {e}")
    
    def _save_results(self):
        """保存结果到Excel文件"""
        if not self.results:
            log.info("没有结果需要保存")
            return
        
        try:
            # 合并所有DataFrame
            all_df = pd.concat(self.results, ignore_index=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"baidu_index_{timestamp}.xlsx"
            file_path = self.output_dir / filename
            
            # 保存到Excel
            all_df.to_excel(file_path, index=False)
            log.info(f"已将 {len(all_df)} 条结果保存到文件: {file_path}")
            
            # 清空结果列表
            self.results = []
            
            # 尝试合并所有批次数据
            self._merge_all_batches(file_path)
            
        except Exception as e:
            log.error(f"保存结果时发生错误: {e}")
    
    def _merge_all_batches(self, output_file):
        """
        合并所有批次数据
        :param output_file: 输出文件路径
        """
        try:
            # 查找所有批次文件
            batch_files = list(self.batch_dir.glob('batch_*.xlsx'))
            if not batch_files:
                log.info("没有批次文件需要合并")
                return
                
            # 合并所有批次文件
            dfs = []
            for batch_file in batch_files:
                try:
                    df = pd.read_excel(batch_file)
                    dfs.append(df)
                    log.debug(f"已读取批次文件: {batch_file}")
                except Exception as e:
                    log.error(f"读取批次文件 {batch_file} 失败: {e}")
            
            if not dfs:
                log.warning("没有有效的批次数据可合并")
                return
                
            # 合并所有DataFrame
            merged_df = pd.concat(dfs, ignore_index=True)
            
            # 保存合并后的数据
            merged_file = self.output_dir / "all_data_merged.xlsx"
            merged_df.to_excel(merged_file, index=False)
            log.info(f"已将所有批次数据 ({len(merged_df)} 条记录) 合并到文件: {merged_file}")
            
        except Exception as e:
            log.error(f"合并批次数据失败: {e}")
    
    def _progress_summary_loop(self):
        """进度汇总循环"""
        log.info("开始进度汇总")
        
        interval = 60  # 默认60秒汇总一次
        while self.running and not self.stop_event.is_set():
            # 检查是否所有Cookie都被锁定
            cookie_status = cookie_rotator.get_status()
            all_cookies_blocked = cookie_status.get('available', 0) == 0 and cookie_status.get('blocked', 0) > 0
            
            # 只有在有可用Cookie时才打印进度摘要
            if not all_cookies_blocked:
                self._print_summary()
            else:
                # 如果所有Cookie都被锁定，只打印简短的状态信息
                wait_info = cookie_status.get('all_blocked_wait_info')
                if wait_info:
                    remaining_mins = wait_info.get('remaining_minutes', 0)
                    if remaining_mins > 0:
                        log.info(f"所有Cookie都被锁定，等待中... 剩余约 {remaining_mins} 分钟")
            
            # 等待下一次汇总
            for _ in range(interval):
                if self.stop_event.is_set():
                    break
                time.sleep(1)
        
        log.info("进度汇总已停止")
    
    def _print_summary(self):
        """打印任务进度汇总"""
        if not self.running or not self.start_time:
            return
        
        try:
            # 计算已经过去的时间
            elapsed_time = time.time() - self.start_time
            elapsed_hours = int(elapsed_time // 3600)
            elapsed_minutes = int((elapsed_time % 3600) // 60)
            elapsed_seconds = int(elapsed_time % 60)
            
            # 计算总任务数
            total_tasks = len(self.tasks)
            completed_tasks = self.completed_tasks + self.failed_tasks
            
            # 计算完成百分比
            completion_percentage = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
            
            # 计算速度(每分钟完成的任务数)
            speed = completed_tasks / (elapsed_time / 60) if elapsed_time > 0 else 0
            
            # 计算剩余时间
            remaining_tasks = total_tasks - completed_tasks
            remaining_minutes = remaining_tasks / speed if speed > 0 else 0
            remaining_hours = int(remaining_minutes // 60)
            remaining_minutes = int(remaining_minutes % 60)
            
            # 获取Cookie状态
            cookie_status = cookie_rotator.get_status()
            available_cookies = cookie_status.get('available', 0)
            blocked_cookies = cookie_status.get('blocked', 0)
            
            # 计算已保存的批次数量
            saved_batches = self.batch_number - (1 if self.current_batch else 0)
            
            # 打印摘要
            summary = (
                f"\n========= 爬取进度摘要 =========\n"
                f"总任务数: {total_tasks}\n"
                f"已完成: {self.completed_tasks} 成功, {self.failed_tasks} 失败, 总计: {completed_tasks}\n"
                f"完成百分比: {completion_percentage:.2f}%\n"
                f"已耗时: {elapsed_hours}小时 {elapsed_minutes}分钟 {elapsed_seconds}秒\n"
                f"处理速度: {speed:.2f} 任务/分钟\n"
                f"预计剩余时间: {remaining_hours}小时 {remaining_minutes}分钟\n"
                f"已保存批次: {saved_batches}, 当前批次数据量: {len(self.current_batch)}\n"
                f"Cookie状态: {available_cookies}个可用, {blocked_cookies}个锁定\n"
                f"================================\n"
            )
            
            log.info(summary)
        
        except Exception as e:
            log.error(f"生成进度摘要时发生错误: {e}")


# 创建任务管理器单例
task_manager = TaskManager() 