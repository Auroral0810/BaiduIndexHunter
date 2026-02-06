"""
统计服务
提供统计数据的业务逻辑处理
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date

from src.core.logger import log
from src.data.repositories.statistics_repository import statistics_repo
from src.data.repositories.task_repository import task_repo

class StatisticsService:
    """统计服务类"""
    
    def __init__(self):
        self.stats_repo = statistics_repo
        self.task_repo = task_repo

    def get_task_summary(self, days: int) -> Dict[str, Any]:
        """获取任务统计摘要"""
        start_date = None
        if days > 0:
            start_date = datetime.now() - timedelta(days=days)
            
        total_tasks = self.task_repo.count_tasks(start_date)
        status_counts_list = self.task_repo.get_task_counts_by_status(start_date)
        type_results = self.task_repo.get_task_counts_by_type(start_date)
        daily_results = self.task_repo.get_daily_task_counts(start_date)
        
        # 转换状态计数格式
        status_counts = {
            'completed': 0, 'running': 0, 'pending': 0,
            'paused': 0, 'failed': 0, 'cancelled': 0
        }
        for item in status_counts_list:
            status = item['status']
            if status in status_counts:
                status_counts[status] = item['count']
                
        return {
            'total_tasks': total_tasks,
            'completed_tasks': status_counts['completed'],
            'running_tasks': status_counts['running'],
            'pending_tasks': status_counts['pending'] + status_counts['paused'],
            'failed_tasks': status_counts['failed'] + status_counts['cancelled'],
            'task_types': type_results,
            'daily_tasks': daily_results
        }
        
    def get_task_statistics(self, task_id: str) -> List[Dict[str, Any]]:
        """获取指定任务的详细统计数据"""
        # Fetch models
        stats = self.stats_repo.get_task_statistics(task_id)
        # Convert to dicts for API response compatibility
        results = []
        for stat in stats:
            data = stat.model_dump()
            if isinstance(data.get('create_time'), (date, datetime)):
                data['create_time'] = data['create_time'].strftime('%Y-%m-%d %H:%M:%S')
            results.append(data)
        return results

    def get_spider_statistics(self, stat_date_str: Optional[str] = None, task_type: Optional[str] = None, start_date_str: Optional[str] = None, end_date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取爬虫统计数据"""
        stat_date = None
        start_date = None
        end_date = None
        
        try:
            if stat_date_str:
                stat_date = datetime.strptime(stat_date_str, '%Y-%m-%d').date()
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError as e:
            log.warning(f"Invalid date format in get_spider_statistics: {e}")
            
        stats = self.stats_repo.get_spider_statistics(stat_date, task_type, start_date, end_date)
        
        results = []
        for stat in stats:
            data = stat.model_dump()
            # Explicitly format date to avoid GMT strings in JSON
            if isinstance(data.get('stat_date'), (date, datetime)):
                data['stat_date'] = data['stat_date'].strftime('%Y-%m-%d')
            results.append(data)
        return results

    def get_keyword_statistics(self, task_id: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """获取关键词统计"""
        keywords = self.stats_repo.get_keyword_statistics(task_id, limit)
        return {
            'keywords': keywords,
            'total': len(keywords)
        }

    def get_city_statistics(self, city_name: Optional[str] = None, task_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取城市统计"""
        # Repo already returns dicts
        return self.stats_repo.get_city_statistics(city_name, task_type, limit)

    def get_dashboard_data(self, days: int, start_date_str: Optional[str] = None, end_date_str: Optional[str] = None) -> Dict[str, Any]:
        """获取大屏数据"""
        # Calculate date range
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=30)
        elif days == -1:
            end_date = datetime.now().date()
            start_date = date(2000, 1, 1)
        else:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
        task_types = self.stats_repo.get_task_types()
        overall_stats = self.stats_repo.get_dashboard_overall(start_date, end_date)
        daily_trend = self.stats_repo.get_dashboard_daily_trend(start_date, end_date)
        
        # New aggregations
        by_task_type = self.stats_repo.get_stats_by_task_type(start_date, end_date)
        task_type_trends = self.stats_repo.get_task_type_trends(start_date, end_date, task_types)
        success_rate_comparison = self.stats_repo.get_success_rate_comparison(start_date, end_date)
        avg_duration_comparison = self.stats_repo.get_avg_duration_comparison(start_date, end_date)
        data_volume_comparison = self.stats_repo.get_data_volume_comparison(start_date, end_date)
        
        return {
            'task_types': task_types,
            'overall': overall_stats,
            'daily_trend': daily_trend,
            'by_task_type': by_task_type,
            'task_type_trends': task_type_trends,
            'success_rate_comparison': success_rate_comparison,
            'avg_duration_comparison': avg_duration_comparison,
            'data_volume_comparison': data_volume_comparison
        }

# Global Instance
statistics_service = StatisticsService()
