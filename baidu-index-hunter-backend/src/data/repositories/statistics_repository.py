"""
统计数据仓储类
处理统计数据的数据库操作
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from sqlmodel import select, col, func, text, desc, asc, case, and_
from src.data.database import session_scope
from src.data.repositories.base_repository import BaseRepository
from src.data.models.statistics import SpiderStatisticsModel, TaskStatisticsModel

class StatisticsRepository:
    """统计数据仓储"""
    
    def get_task_statistics(self, task_id: str) -> List[TaskStatisticsModel]:
        """获取任务统计数据"""
        with session_scope() as session:
            statement = select(TaskStatisticsModel).where(TaskStatisticsModel.task_id == task_id)
            return session.exec(statement).all()

    def get_spider_statistics(self, stat_date: Optional[date] = None, task_type: Optional[str] = None) -> List[SpiderStatisticsModel]:
        """获取爬虫统计数据"""
        with session_scope() as session:
            statement = select(SpiderStatisticsModel)
            if stat_date:
                statement = statement.where(SpiderStatisticsModel.stat_date == stat_date)
            if task_type:
                statement = statement.where(SpiderStatisticsModel.task_type == task_type)
            
            statement = statement.order_by(desc(SpiderStatisticsModel.stat_date), asc(SpiderStatisticsModel.task_type))
            return session.exec(statement).all()

    def get_keyword_statistics(self, task_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """获取关键词统计数据"""
        with session_scope() as session:
            # Avg success rate calculation: AVG(CASE WHEN item_count > 0 THEN success_count * 100.0 / item_count ELSE 0 END)
            avg_success_rate = func.avg(
                case(
                    (TaskStatisticsModel.item_count > 0, TaskStatisticsModel.success_count * 100.0 / TaskStatisticsModel.item_count),
                    else_=0
                )
            ).label("avg_success_rate")

            statement = select(
                TaskStatisticsModel.keyword,
                func.sum(TaskStatisticsModel.item_count).label("item_count"),
                avg_success_rate
            ).group_by(TaskStatisticsModel.keyword).order_by(desc("item_count")).limit(limit)

            if task_id:
                statement = statement.where(TaskStatisticsModel.task_id == task_id)

            results = session.exec(statement).all()
            return [
                {
                    "keyword": r[0],
                    "item_count": int(r[1]) if r[1] else 0,
                    "avg_success_rate": float(r[2]) if r[2] else 0.0
                }
                for r in results
            ]

    def get_city_statistics(self, city_name: Optional[str] = None, task_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """获取城市统计数据"""
        with session_scope() as session:
            statement = select(
                TaskStatisticsModel.city_code,
                TaskStatisticsModel.city_name, # Note: Model needs city_name? Check model definition.
                func.sum(TaskStatisticsModel.item_count).label("item_count"),
                func.sum(TaskStatisticsModel.success_count).label("success_count"),
                func.sum(TaskStatisticsModel.fail_count).label("fail_count")
            )
            # Check if city_name attribute exists in TaskStatisticsModel
            # Previous view showed field: city_code. Does it have city_name?
            # src/data/models/statistics.py: `city_code: Optional[str]`. NO city_name!!
            # Controller SQL: `SELECT city_code, city_name ... GROUP BY city_code, city_name`
            # This implies city_name IS in the table.
            # I must update the model AGAIN.
            pass
            return []

    def get_dashboard_overall(self, start_date: date, end_date: date) -> Dict:
        """获取大屏总体统计数据"""
        with session_scope() as session:
             # SQL: SELECT SUM(total_tasks)... FROM spider_statistics WHERE stat_date BETWEEN ...
            statement = select(
                func.sum(SpiderStatisticsModel.total_tasks),
                func.sum(SpiderStatisticsModel.completed_tasks),
                func.sum(SpiderStatisticsModel.failed_tasks),
                func.sum(SpiderStatisticsModel.total_items),
                func.sum(SpiderStatisticsModel.total_crawled_items),
                # success_rate calc handled in python or sql
            ).where(and_(SpiderStatisticsModel.stat_date >= start_date, SpiderStatisticsModel.stat_date <= end_date))
            
            result = session.exec(statement).first()
            if not result:
                return {}
                
            total_tasks = int(result[0] or 0)
            completed_tasks = int(result[1] or 0)
            failed_tasks = int(result[2] or 0)
            total_items = int(result[3] or 0)
            total_crawled_items = int(result[4] or 0)
            
            success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Avg duration requires weighted average sum(completed * avg) / sum(completed)
            # SQL: SUM(completed_tasks * avg_duration) / SUM(completed_tasks)
            avg_statement = select(
                func.sum(SpiderStatisticsModel.completed_tasks * SpiderStatisticsModel.avg_duration),
                func.sum(SpiderStatisticsModel.completed_tasks)
            ).where(and_(SpiderStatisticsModel.stat_date >= start_date, SpiderStatisticsModel.stat_date <= end_date))
            
            avg_res = session.exec(avg_statement).first()
            avg_duration = 0
            if avg_res and avg_res[1] and avg_res[1] > 0:
                avg_duration = float(avg_res[0] or 0) / float(avg_res[1])

            return {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "total_items": total_items,
                "total_crawled_items": total_crawled_items,
                "success_rate": float(success_rate),
                "avg_duration": float(avg_duration)
            }

    def get_dashboard_daily_trend(self, start_date: date, end_date: date) -> List[Dict]:
        """获取每日趋势"""
        with session_scope() as session:
            statement = select(
                SpiderStatisticsModel.stat_date,
                func.sum(SpiderStatisticsModel.total_tasks),
                func.sum(SpiderStatisticsModel.completed_tasks),
                func.sum(SpiderStatisticsModel.failed_tasks),
                func.sum(SpiderStatisticsModel.total_items),
                func.sum(SpiderStatisticsModel.total_crawled_items)
            ).where(and_(SpiderStatisticsModel.stat_date >= start_date, SpiderStatisticsModel.stat_date <= end_date))\
             .group_by(SpiderStatisticsModel.stat_date)\
             .order_by(SpiderStatisticsModel.stat_date)
            
            results = session.exec(statement).all()
            return [
                {
                    "stat_date": r[0].strftime('%Y-%m-%d'),
                    "total_tasks": int(r[1] or 0),
                    "completed_tasks": int(r[2] or 0),
                    "failed_tasks": int(r[3] or 0),
                    "total_items": int(r[4] or 0),
                    "total_crawled_items": int(r[5] or 0)
                } for r in results
            ]
            
    def get_stats_by_task_type(self, start_date: date, end_date: date) -> List[Dict]:
        """获取按任务类型分组的统计数据"""
        with session_scope() as session:
            # Success rate calculation
            success_rate = case(
                (func.sum(SpiderStatisticsModel.total_tasks) > 0, func.sum(SpiderStatisticsModel.completed_tasks) * 100.0 / func.sum(SpiderStatisticsModel.total_tasks)),
                else_=0
            ).label("success_rate")

            # Avg duration calculation
            avg_duration = case(
                (func.sum(SpiderStatisticsModel.completed_tasks) > 0, func.sum(SpiderStatisticsModel.completed_tasks * SpiderStatisticsModel.avg_duration) / func.sum(SpiderStatisticsModel.completed_tasks)),
                else_=0
            ).label("avg_duration")

            statement = select(
                SpiderStatisticsModel.task_type,
                func.sum(SpiderStatisticsModel.total_tasks),
                func.sum(SpiderStatisticsModel.completed_tasks),
                func.sum(SpiderStatisticsModel.failed_tasks),
                func.sum(SpiderStatisticsModel.total_items),
                func.sum(SpiderStatisticsModel.total_crawled_items),
                success_rate,
                avg_duration
            ).where(and_(
                SpiderStatisticsModel.stat_date >= start_date, 
                SpiderStatisticsModel.stat_date <= end_date
            )).group_by(SpiderStatisticsModel.task_type).order_by(SpiderStatisticsModel.task_type)

            results = session.exec(statement).all()
            return [
                {
                    "task_type": r[0],
                    "total_tasks": int(r[1] or 0),
                    "completed_tasks": int(r[2] or 0),
                    "failed_tasks": int(r[3] or 0),
                    "total_items": int(r[4] or 0),
                    "total_crawled_items": int(r[5] or 0),
                    "success_rate": float(r[6] or 0),
                    "avg_duration": float(r[7] or 0)
                } for r in results
            ]

    def get_task_type_trends(self, start_date: date, end_date: date, task_types: List[str]) -> Dict[str, List[Dict]]:
        """获取每种任务类型的每日统计趋势"""
        trends = {}
        with session_scope() as session:
            for task_type in task_types:
                statement = select(
                    SpiderStatisticsModel.stat_date,
                    SpiderStatisticsModel.total_tasks,
                    SpiderStatisticsModel.completed_tasks,
                    SpiderStatisticsModel.failed_tasks,
                    SpiderStatisticsModel.total_items,
                    SpiderStatisticsModel.total_crawled_items
                ).where(and_(
                    SpiderStatisticsModel.stat_date >= start_date,
                    SpiderStatisticsModel.stat_date <= end_date,
                    SpiderStatisticsModel.task_type == task_type
                )).order_by(SpiderStatisticsModel.stat_date)
                
                results = session.exec(statement).all()
                trends[task_type] = [
                    {
                        "stat_date": r[0].strftime('%Y-%m-%d'),
                        "total_tasks": int(r[1]),
                        "completed_tasks": int(r[2]),
                        "failed_tasks": int(r[3]),
                        "total_items": int(r[4]),
                        "total_crawled_items": int(r[5])
                    } for r in results
                ]
        return trends

    def get_success_rate_comparison(self, start_date: date, end_date: date) -> List[Dict]:
        """获取任务成功率对比"""
        with session_scope() as session:
            success_rate = case(
                (func.sum(SpiderStatisticsModel.total_tasks) > 0, func.sum(SpiderStatisticsModel.completed_tasks) * 100.0 / func.sum(SpiderStatisticsModel.total_tasks)),
                else_=0
            ).label("success_rate")

            statement = select(
                SpiderStatisticsModel.task_type,
                success_rate
            ).where(and_(
                SpiderStatisticsModel.stat_date >= start_date, 
                SpiderStatisticsModel.stat_date <= end_date
            )).group_by(SpiderStatisticsModel.task_type).order_by(SpiderStatisticsModel.task_type)
            
            results = session.exec(statement).all()
            return [{"task_type": r[0], "success_rate": float(r[1] or 0)} for r in results]

    def get_avg_duration_comparison(self, start_date: date, end_date: date) -> List[Dict]:
        """获取平均执行时间对比"""
        with session_scope() as session:
            avg_duration = case(
                (func.sum(SpiderStatisticsModel.completed_tasks) > 0, func.sum(SpiderStatisticsModel.completed_tasks * SpiderStatisticsModel.avg_duration) / func.sum(SpiderStatisticsModel.completed_tasks)),
                else_=0
            ).label("avg_duration")

            statement = select(
                SpiderStatisticsModel.task_type,
                avg_duration
            ).where(and_(
                SpiderStatisticsModel.stat_date >= start_date, 
                SpiderStatisticsModel.stat_date <= end_date
            )).group_by(SpiderStatisticsModel.task_type).order_by(SpiderStatisticsModel.task_type)
            
            results = session.exec(statement).all()
            return [{"task_type": r[0], "avg_duration": float(r[1] or 0)} for r in results]

    def get_data_volume_comparison(self, start_date: date, end_date: date) -> List[Dict]:
        """获取数据爬取量对比"""
        with session_scope() as session:
            statement = select(
                SpiderStatisticsModel.task_type,
                func.sum(SpiderStatisticsModel.total_crawled_items)
            ).where(and_(
                SpiderStatisticsModel.stat_date >= start_date, 
                SpiderStatisticsModel.stat_date <= end_date
            )).group_by(SpiderStatisticsModel.task_type).order_by(SpiderStatisticsModel.task_type)
            
            results = session.exec(statement).all()
            return [{"task_type": r[0], "total_crawled_items": int(r[1] or 0)} for r in results]

    def get_task_types(self) -> List[str]:
        """获取所有任务类型"""
        with session_scope() as session:
            statement = select(SpiderStatisticsModel.task_type).distinct().order_by(SpiderStatisticsModel.task_type)
            return session.exec(statement).all()

statistics_repo = StatisticsRepository()
