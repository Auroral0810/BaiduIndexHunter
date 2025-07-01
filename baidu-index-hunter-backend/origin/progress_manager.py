"""
爬取进度管理模块
"""
import os
import pandas as pd
import threading
from datetime import datetime
from pathlib import Path
from utils.logger import log
import time


class ProgressManager:
    """爬取进度管理器，管理爬取任务的进度，使用CSV文件存储"""
    
    def __init__(self, progress_file=None):
        """
        初始化爬取进度管理器
        :param progress_file: 进度文件路径，默认为项目根目录下的data/crawler_progress.csv
        """
        if progress_file is None:
            progress_file = Path(__file__).parent.parent / 'data' / 'crawler_progress.csv'
        
        self.progress_file = Path(progress_file)
        # 确保父目录存在
        os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
        self.progress_df = None
        self.lock = threading.RLock()
        # 添加缓存字典，用于快速查询任务是否完成
        self.completed_tasks_cache = {}
        # 添加批量保存相关变量
        self.pending_updates = []
        self.last_save_time = time.time()
        self.save_interval = 10  # 10秒保存一次
        self.max_pending_updates = 100  # 累积100条记录就保存
        self.load_progress()
        log.info(f"进度管理器初始化完成，使用进度文件: {self.progress_file}")
    
    def load_progress(self):
        """加载进度文件"""
        try:
            if os.path.exists(self.progress_file) and os.path.getsize(self.progress_file) > 0:
                with self.lock:
                    try:
                        # 使用更高效的方式加载CSV文件
                        log.info(f"开始加载进度文件: {self.progress_file}")
                        start_time = time.time()
                        
                        # 只读取需要的列
                        self.progress_df = pd.read_csv(
                            self.progress_file,
                            usecols=['keyword', 'area', 'year', 'index_type', 'status', 'timestamp']
                        )
                        
                        load_time = time.time() - start_time
                        log.info(f"已从文件加载 {len(self.progress_df)} 条进度记录，耗时 {load_time:.2f} 秒")
                        
                        # 重建缓存
                        cache_start = time.time()
                        self._rebuild_cache()
                        cache_time = time.time() - cache_start
                        log.info(f"重建缓存耗时 {cache_time:.2f} 秒")
                    except Exception as e:
                        log.error(f"进度文件解析失败: {e}，初始化为空DataFrame")
                        self._init_empty_df()
            else:
                log.warning(f"进度文件不存在或为空: {self.progress_file}，初始化为空DataFrame")
                self._init_empty_df()
                self.save_progress()
        except Exception as e:
            log.error(f"加载爬取进度文件失败: {e}")
            self._init_empty_df()
    
    def _rebuild_cache(self):
        """重建任务完成状态缓存"""
        self.completed_tasks_cache = {}
        if self.progress_df is None or self.progress_df.empty:
            return
            
        # 筛选出所有状态为success的记录
        success_df = self.progress_df[self.progress_df['status'] == 'success']
        
        # 使用向量化操作创建键值对
        if not success_df.empty:
            # 直接从DataFrame构建缓存，避免循环
            keys = list(zip(
                success_df['keyword'], 
                success_df['area'], 
                success_df['year'], 
                success_df['index_type']
            ))
            # 构建缓存字典
            self.completed_tasks_cache = {key: True for key in keys}
            
        # log.info(f"已重建任务完成状态缓存，共 {len(self.completed_tasks_cache)} 条记录")
    
    def _init_empty_df(self):
        """初始化空的进度DataFrame"""
        self.progress_df = pd.DataFrame(columns=[
            'keyword', 'area', 'year', 'index_type', 'status', 'timestamp'
        ])
        self.completed_tasks_cache = {}
    
    def save_progress(self):
        """保存进度到文件"""
        try:
            with self.lock:
                # 读取现有文件内容，以便合并
                existing_df = None
                try:
                    if os.path.exists(self.progress_file) and os.path.getsize(self.progress_file) > 0:
                        existing_df = pd.read_csv(self.progress_file)
                except Exception:
                    existing_df = None
                
                if existing_df is not None and not existing_df.empty:
                    # 合并新的和现有的进度数据，保留已成功状态的记录
                    combined_df = pd.concat([existing_df, self.progress_df])
                    # 对每组keyword, area, year, index_type，保留status为'success'的行，否则保留最新的行
                    combined_df = combined_df.sort_values(['timestamp', 'status'], 
                                           ascending=[True, False])  # 'success'在排序中优先级高于'failed'
                    # 删除重复项，保留第一个出现的（即'success'或最新的记录）
                    combined_df = combined_df.drop_duplicates(
                        subset=['keyword', 'area', 'year', 'index_type'], 
                        keep='first')
                    self.progress_df = combined_df
                
                # 保存到CSV文件
                self.progress_df.to_csv(self.progress_file, index=False)
                
                # 重建缓存
                self._rebuild_cache()
                
        except Exception as e:
            log.error(f"保存爬取进度文件失败: {e}")
    
    def is_completed(self, keyword, area, year, index_type="search"):
        """
        检查任务是否已完成
        :param keyword: 关键词
        :param area: 地区代码
        :param year: 年份
        :param index_type: 指数类型，可选值：'search'或'trend'
        :return: 是否已完成
        """
        # 只检查缓存，不再查询DataFrame
        key = (keyword, area, year, index_type)
        return key in self.completed_tasks_cache
    
    def mark_completed(self, keyword, area, year, index_type="search", status="success"):
        """
        标记任务为已完成
        :param keyword: 关键词
        :param area: 地区代码
        :param year: 年份
        :param index_type: 指数类型，可选值：'search'或'trend'
        :param status: 状态，可选值：'success'或'failed'
        """
        with self.lock:
            # 创建新的记录
            new_record = {
                'keyword': keyword,
                'area': area,
                'year': year,
                'index_type': index_type,
                'status': status,
                'timestamp': datetime.now().isoformat()
            }
            
            # 添加到现有DataFrame
            self.progress_df = pd.concat([self.progress_df, pd.DataFrame([new_record])], ignore_index=True)
            
            # 更新缓存
            if status == 'success':
                key = (keyword, area, year, index_type)
                self.completed_tasks_cache[key] = True
            
            # 添加到待保存列表
            self.pending_updates.append(new_record)
            
            # 统计当前完成的任务数
            success_count = len(self.progress_df[self.progress_df['status'] == 'success'])
            failed_count = len(self.progress_df[self.progress_df['status'] == 'failed'])
            
            # 检查是否需要保存进度
            current_time = time.time()
            should_save = (
                len(self.pending_updates) >= self.max_pending_updates or 
                current_time - self.last_save_time >= self.save_interval
            )
            
            if should_save:
                self.save_progress()
                self.pending_updates = []
                self.last_save_time = current_time
                log.info(f"批量保存进度，当前成功: {success_count}, 失败: {failed_count}")
            
            if status == 'success':
                log.info(f"任务已标记为成功: {keyword}, {area}, {year}, {index_type}. 当前成功: {success_count}, 失败: {failed_count}")
            else:
                log.debug(f"任务已标记为失败: {keyword}, {area}, {year}, {index_type}. 当前成功: {success_count}, 失败: {failed_count}")
    
    def get_progress_stats(self):
        """
        获取进度统计信息
        :return: 包含完成和失败任务数的字典
        """
        with self.lock:
            if self.progress_df is None or self.progress_df.empty:
                return {
                    'total': 0,
                    'success': 0,
                    'failed': 0,
                    'completion_rate': "0%"
                }
            
            success_count = len(self.progress_df[self.progress_df['status'] == 'success'])
            failed_count = len(self.progress_df[self.progress_df['status'] == 'failed'])
            total_count = len(self.progress_df)
            
            return {
                'total': total_count,
                'success': success_count,
                'failed': failed_count,
                'completion_rate': f"{success_count / total_count * 100:.2f}%" if total_count > 0 else "0%"
            }
    
    def reset_progress(self):
        """重置进度（慎用）"""
        with self.lock:
            self._init_empty_df()
            self.save_progress()
            log.warning("已重置爬取进度")

    def get_progress_file_path(self):
        """获取进度文件路径"""
        return str(self.progress_file)


# 创建进度管理器实例，而不是单例
# 注意：main.py会创建一个新的实例，使用指定的进度文件路径
progress_manager = ProgressManager() 