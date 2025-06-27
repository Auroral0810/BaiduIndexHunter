"""
爬取进度管理模块
"""
import os
import json
import threading
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
        
        self.progress_file = progress_file
        # 确保父目录存在
        os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
        self.progress = {}
        self.lock = threading.RLock()
        self.load_progress()
    
    def load_progress(self):
        """加载进度文件"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    self.progress = json.load(f)
                log.info(f"已加载爬取进度文件，包含 {len(self.progress)} 条记录")
            else:
                log.info(f"爬取进度文件不存在，将创建新文件: {self.progress_file}")
                self.progress = {}
                self.save_progress()
        except Exception as e:
            log.error(f"加载爬取进度文件失败: {e}")
            self.progress = {}
    
    def save_progress(self):
        """保存进度到文件"""
        try:
            with self.lock:
                with open(self.progress_file, 'w', encoding='utf-8') as f:
                    json.dump(self.progress, f, ensure_ascii=False, indent=2)
                log.debug(f"已保存爬取进度，包含 {len(self.progress)} 条记录")
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
        key = f"{keyword}_{area}_{year}"
        with self.lock:
            if key in self.progress:
                record = self.progress[key]
                return (record.get('status') == 'success' and 
                        record.get('index_type') == index_type and 
                        record.get('keyword') == keyword and 
                        record.get('area') == area and 
                        record.get('year') == year)
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
        key = f"{keyword}_{area}_{year}"
        with self.lock:
            self.progress[key] = {
                'keyword': keyword,
                'area': area,
                'index_type': index_type,
                'year': year,
                'status': status,
                'timestamp': datetime.now().isoformat()
            }
            # 每标记完成一项，就保存一次进度
            self.save_progress()
    
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