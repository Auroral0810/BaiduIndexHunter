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
        self.results_buffer = []
        self.progress_summary_thread = None
        self.output_dir = Path(__file__).parent.parent / 'output'
        os.makedirs(self.output_dir, exist_ok=True)
        self.batch_size = 500  # 增加批量写入的大小，从100增加到500
        
        # 固定CSV结果文件路径
        self.results_file = Path('/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/data/result_data.csv')
        
        # 确保data目录存在
        os.makedirs(os.path.dirname(self.results_file), exist_ok=True)
        
        # 是否需要写入CSV文件头
        self.need_header = not os.path.exists(self.results_file) or os.path.getsize(self.results_file) == 0
    
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
        total = len(keywords) * len(areas) * len(years) * len(index_types)
        
        log.info(f"正在创建爬取任务，理论总数: {total}...")

        # 先重新加载进度文件，确保读取最新进度
        from spider.progress_manager import progress_manager
        progress_manager.load_progress()
        log.info(f"已从文件重新加载进度数据: {progress_manager.progress_file}")
        
        # 直接从缓存获取所有已完成的任务，避免重复查询
        completed_tasks = progress_manager.completed_tasks_cache
        
        # 批量创建任务
        for keyword in keywords:
            keyword_tasks = []
            
            for area in areas:
                for year in years:
                    for index_type in index_types:
                        # 使用缓存快速检查任务是否已完成
                        key = (keyword, area, year, index_type)
                        if key not in completed_tasks:
                            # 添加到任务列表
                            task = {
                                'keyword': keyword,
                                'area': area,
                                'year': year,
                                'index_type': index_type
                            }
                            keyword_tasks.append(task)
            
            # 添加当前关键词的所有未完成任务
            tasks.extend(keyword_tasks)
        
        skipped = total - len(tasks)
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
        self.results_buffer = []
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
        
        # 保存缓冲区中的数据
        if self.results_buffer:
            self._flush_results_buffer()
        
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
            # 每个cookie可以支持多个线程，增加到8个线程/cookie
            workers = min(available_workers, cookies_count * 2)
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
                            with self.lock:
                                self.results_buffer.append(result)
                                # 检查是否需要将缓冲区的数据写入文件
                                if len(self.results_buffer) >= self.batch_size:
                                    self._flush_results_buffer()
                        self.completed_tasks += 1
                    except Exception as exc:
                        log.error(f"任务执行失败: {task}, 异常: {exc}")
                        self.failed_tasks += 1
            
            # 保存缓冲区中剩余的数据
            if self.results_buffer:
                self._flush_results_buffer()
            
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
                        # 标记任务完成
                        progress_manager.mark_completed(keyword, area, year, index_type, status='success')
                        return df
                    else:
                        # 标记任务失败
                        progress_manager.mark_completed(keyword, area, year, index_type, status='failed')
                        return None
                else:
                    # 标记任务失败，但不记录详细日志
                    progress_manager.mark_completed(keyword, area, year, index_type, status='failed')
                    return None
            
            elif index_type == 'trend':
                data = baidu_index_api.get_trend_index(keyword, area, start_date, end_date)
                if data:
                    # 处理数据
                    df = data_processor.process_trend_index_data(data, area, keyword, year)
                    
                    if not df.empty:
                        # 标记任务完成
                        progress_manager.mark_completed(keyword, area, year, index_type, status='success')
                        return df
                    else:
                        # 标记任务失败
                        progress_manager.mark_completed(keyword, area, year, index_type, status='failed')
                        return None
                else:
                    # 标记任务失败，但不记录详细日志
                    progress_manager.mark_completed(keyword, area, year, index_type, status='failed')
                    return None
            
            else:
                # 标记任务失败
                progress_manager.mark_completed(keyword, area, year, index_type, status='failed')
                return None
        
        except Exception as e:
            # 只记录关键错误，减少日志量
            if 'timeout' not in str(e).lower() and 'connection' not in str(e).lower():
                log.error(f"处理任务失败: {keyword}, {area}, {year}, {index_type}, 错误: {e}")
            # 标记任务失败
            progress_manager.mark_completed(keyword, area, year, index_type, status='failed')
            return None
    
    def _flush_results_buffer(self):
        """将缓冲区中的数据追加到CSV文件"""
        if not self.results_buffer:
            return
        
        try:
            # 合并缓冲区中的所有DataFrame
            buffer_df = pd.concat(self.results_buffer, ignore_index=True)
            
            # 追加到CSV文件
            buffer_df.to_csv(self.results_file, mode='a', header=self.need_header, index=False)
            log.info(f"已将 {len(buffer_df)} 条结果追加到CSV文件: {self.results_file}")
            
            # 首次写入后不再需要写入文件头
            self.need_header = False
            
            # 清空缓冲区
            self.results_buffer = []
            
        except Exception as e:
            log.error(f"追加数据到CSV文件失败: {e}")
    
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
            
            # 获取当前缓冲区大小和已写入数据量
            buffer_size = len(self.results_buffer)
            try:
                # 获取已写入的数据量
                file_size = os.path.getsize(self.results_file) if os.path.exists(self.results_file) else 0
                file_size_mb = file_size / (1024 * 1024)  # 转换为MB
                
                # 如果文件存在且不为空，尝试读取前几行以估算记录数
                record_count = "未知"
                if file_size > 0:
                    try:
                        # 只读取文件的前部分来估算行数
                        with open(self.results_file, 'rb') as f:
                            chunk = f.read(min(1024*1024, file_size))  # 读取最多1MB
                            lines = chunk.count(b'\n')
                            if file_size > 1024*1024:
                                # 估算总行数
                                estimated_lines = int(lines * (file_size / len(chunk)))
                                record_count = f"估计 {estimated_lines} 条记录"
                            else:
                                record_count = f"{lines} 条记录"
                    except Exception:
                        record_count = "无法读取"
            except Exception:
                file_size_mb = 0
            
            # 打印摘要
            summary = (
                f"\n========= 爬取进度摘要 =========\n"
                f"总任务数: {total_tasks}\n"
                f"已完成: {self.completed_tasks} 成功, {self.failed_tasks} 失败, 总计: {completed_tasks}\n"
                f"完成百分比: {completion_percentage:.2f}%\n"
                f"已耗时: {elapsed_hours}小时 {elapsed_minutes}分钟 {elapsed_seconds}秒\n"
                f"处理速度: {speed:.2f} 任务/分钟\n"
                f"预计剩余时间: {remaining_hours}小时 {remaining_minutes}分钟\n"
                f"当前缓冲区: {buffer_size} 条数据\n"
                f"结果文件: {self.results_file}, 大小: {file_size_mb:.2f}MB, {record_count}\n"
                f"Cookie状态: {available_cookies}个可用, {blocked_cookies}个锁定\n"
                f"================================\n"
            )
            
            log.info(summary)
        
        except Exception as e:
            log.error(f"生成进度摘要时发生错误: {e}")


# 创建任务管理器单例
task_manager = TaskManager() 