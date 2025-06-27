"""
爬取进度管理模块
"""
import os
import json
import threading
import fcntl
from datetime import datetime
from pathlib import Path
from utils.logger import log


class ProgressManager:
    """爬取进度管理器，管理爬取任务的进度"""
    
    def __init__(self, progress_file=None):
        """
        初始化爬取进度管理器
        :param progress_file: 进度文件路径，默认为项目根目录下的data/crawler_progress.json
        """
        if progress_file is None:
            progress_file = Path(__file__).parent.parent / 'data' / 'crawler_progress.json'
        
        self.progress_file = Path(progress_file)
        # 确保父目录存在
        os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
        self.progress = {}
        self.lock = threading.RLock()
        self.load_progress()
        log.info(f"进度管理器初始化完成，使用进度文件: {self.progress_file}")
    
    def load_progress(self):
        """加载进度文件"""
        try:
            if os.path.exists(self.progress_file):
                with self.lock:
                    with open(self.progress_file, 'r', encoding='utf-8') as f:
                        # 使用文件锁保证互斥访问
                        fcntl.flock(f, fcntl.LOCK_SH)
                        try:
                            self.progress = json.load(f)
                            log.info(f"已从文件加载 {len(self.progress)} 条进度记录")
                        except json.JSONDecodeError as e:
                            log.error(f"进度文件解析失败: {e}，初始化为空进度")
                            self.progress = {}
                        finally:
                            fcntl.flock(f, fcntl.LOCK_UN)
            else:
                log.warning(f"进度文件不存在: {self.progress_file}，初始化为空进度")
                self.progress = {}
                self.save_progress()
        except Exception as e:
            log.error(f"加载爬取进度文件失败: {e}")
            self.progress = {}
    
    def save_progress(self):
        """保存进度到文件"""
        try:
            with self.lock:
                # 先读取最新的进度文件内容，以免覆盖其他进程的更新
                existing_progress = {}
                if os.path.exists(self.progress_file):
                    with open(self.progress_file, 'r', encoding='utf-8') as f:
                        # 使用文件锁保证互斥访问
                        fcntl.flock(f, fcntl.LOCK_SH)
                        try:
                            existing_progress = json.load(f)
                        except json.JSONDecodeError:
                            # 文件可能为空或格式错误
                            existing_progress = {}
                        finally:
                            fcntl.flock(f, fcntl.LOCK_UN)
                
                # 合并进度数据
                # 策略：对于同一个key，如果旧数据是success，保留旧数据；否则使用新数据
                for key, value in self.progress.items():
                    if key in existing_progress:
                        if existing_progress[key].get('status') != 'success':
                            existing_progress[key] = value
                    else:
                        existing_progress[key] = value
                
                # 更新内存中的进度
                self.progress = existing_progress
                
                # 写入文件
                with open(self.progress_file, 'w', encoding='utf-8') as f:
                    # 使用文件锁保证互斥访问
                    fcntl.flock(f, fcntl.LOCK_EX)
                    try:
                        json.dump(self.progress, f, ensure_ascii=False, indent=2)
                    finally:
                        fcntl.flock(f, fcntl.LOCK_UN)
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
        # 使用不同格式的key进行尝试
        key_with_type = f"{keyword}_{area}_{year}_{index_type}"  # 新格式，包含index_type
        key_without_type = f"{keyword}_{area}_{year}"  # 旧格式，不包含index_type
        
        with self.lock:
            # 检查新格式的key
            if key_with_type in self.progress and self.progress[key_with_type].get('status') == 'success':
                return True
                
            # 检查旧格式的key
            if key_without_type in self.progress:
                record = self.progress[key_without_type]
                # 旧格式中必须检查index_type是否匹配或为默认值，并且状态为success
                if (record.get('status') == 'success' and 
                    (record.get('index_type') == index_type or 
                     (record.get('index_type') is None and index_type == 'search'))):
                    return True
                    
        return False
    
    def mark_completed(self, keyword, area, year, index_type="search", status="success"):
        """
        标记任务为已完成
        :param keyword: 关键词
        :param area: 地区代码
        :param year: 年份
        :param index_type: 指数类型，可选值：'search'或'trend'
        :param status: 状态，可选值：'success'或'failed'
        """
        # 使用包含index_type的key，避免覆盖不同类型的记录
        key = f"{keyword}_{area}_{year}_{index_type}"
        with self.lock:
            self.progress[key] = {
                'keyword': keyword,
                'area': area,
                'index_type': index_type,
                'year': year,
                'status': status,
                'timestamp': datetime.now().isoformat()
            }
            
            # 统计当前完成的任务数
            success_count = sum(1 for v in self.progress.values() if v.get('status') == 'success')
            failed_count = sum(1 for v in self.progress.values() if v.get('status') == 'failed')
            
            # 每标记完成一项，就保存一次进度
            self.save_progress()
            
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
            success_count = sum(1 for k, v in self.progress.items() if v.get('status') == 'success')
            failed_count = sum(1 for k, v in self.progress.items() if v.get('status') == 'failed')
            total_count = len(self.progress)
            
            return {
                'total': total_count,
                'success': success_count,
                'failed': failed_count,
                'completion_rate': f"{success_count / total_count * 100:.2f}%" if total_count > 0 else "0%"
            }
    
    def reset_progress(self):
        """重置进度（慎用）"""
        with self.lock:
            self.progress = {}
            self.save_progress()
            log.warning("已重置爬取进度")

    def get_progress_file_path(self):
        """获取进度文件路径"""
        return str(self.progress_file)


# 创建进度管理器实例，而不是单例
# 注意：main.py会创建一个新的实例，使用指定的进度文件路径
progress_manager = ProgressManager() 