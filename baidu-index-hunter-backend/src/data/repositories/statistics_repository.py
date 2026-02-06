"""
统计数据仓储类
处理统计数据的数据库操作
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
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

    def get_spider_statistics(self, stat_date: Optional[date] = None, task_type: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[SpiderStatisticsModel]:
        """获取爬虫统计数据"""
        with session_scope() as session:
            statement = select(SpiderStatisticsModel)
            if stat_date:
                statement = statement.where(SpiderStatisticsModel.stat_date == stat_date)
            else:
                if start_date:
                    statement = statement.where(SpiderStatisticsModel.stat_date >= start_date)
                if end_date:
                    statement = statement.where(SpiderStatisticsModel.stat_date <= end_date)
                    
            if task_type:
                statement = statement.where(SpiderStatisticsModel.task_type == task_type)
            
            statement = statement.order_by(desc(SpiderStatisticsModel.stat_date), asc(SpiderStatisticsModel.task_type))
            return session.exec(statement).all()

    def get_keyword_statistics(self, task_id: Optional[str] = None, limit: int = 100, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict]:
        """获取关键词统计数据"""
        with session_scope() as session:
            statement = select(
                TaskStatisticsModel.keyword,
                func.sum(TaskStatisticsModel.item_count).label("item_count"),
                func.avg(TaskStatisticsModel.avg_value).label("avg_value"),
                func.max(TaskStatisticsModel.max_value).label("max_value"),
                func.min(TaskStatisticsModel.min_value).label("min_value"),
                func.sum(TaskStatisticsModel.success_count).label("success_count")
            ).group_by(TaskStatisticsModel.keyword).order_by(desc("item_count")).limit(limit)

            if task_id:
                statement = statement.where(TaskStatisticsModel.task_id == task_id)
            
            if start_date:
                statement = statement.where(TaskStatisticsModel.create_time >= start_date)
            if end_date:
                # Add one day to end_date to include the full day
                next_day = end_date + timedelta(days=1)
                statement = statement.where(TaskStatisticsModel.create_time < next_day)

            results = session.exec(statement).all()
            return [
                {
                    "keyword": r[0],
                    "item_count": int(r[1]) if r[1] else 0,
                    "avg_value": float(r[2]) if r[2] else 0.0,
                    "max_value": float(r[3]) if r[3] else 0.0,
                    "min_value": float(r[4]) if r[4] else 0.0,
                    "avg_success_rate": (int(r[5] or 0) / int(r[1] or 1) * 100.0) if r[1] else 0.0
                }
                for r in results
            ]

    def get_city_statistics(self, city_name: Optional[str] = None, task_type: Optional[str] = None, limit: int = 100, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict]:
        """获取城市统计数据"""
        with session_scope() as session:
            # 统一处理 NULL 和空值为默认值，确保分组正确
            city_code_col = func.coalesce(func.nullif(TaskStatisticsModel.city_code, ''), '0').label("city_code")
            city_name_col = func.coalesce(func.nullif(TaskStatisticsModel.city_name, ''), '全国').label("city_name")

            statement = select(
                city_code_col,
                city_name_col,
                func.sum(TaskStatisticsModel.item_count).label("item_count"),
                func.sum(TaskStatisticsModel.success_count).label("success_count"),
                func.sum(TaskStatisticsModel.fail_count).label("fail_count")
            )
            
            if task_type:
                from src.data.models.task import SpiderTaskModel
                statement = statement.join(SpiderTaskModel, TaskStatisticsModel.task_id == SpiderTaskModel.task_id)
                statement = statement.where(SpiderTaskModel.task_type == task_type)
                
            if city_name:
                statement = statement.where(TaskStatisticsModel.city_name.contains(city_name))

            if start_date:
                statement = statement.where(TaskStatisticsModel.create_time >= start_date)
            if end_date:
                next_day = end_date + timedelta(days=1)
                statement = statement.where(TaskStatisticsModel.create_time < next_day)
                
            statement = statement.group_by(city_code_col, city_name_col)\
                                 .order_by(desc("item_count")).limit(limit)

            results = session.exec(statement).all()
            return [
                {
                    "city_code": r[0],
                    "city_name": r[1],
                    "item_count": int(r[2] or 0),
                    "success_count": int(r[3] or 0),
                    "fail_count": int(r[4] or 0),
                    "success_rate": (int(r[3] or 0) / int(r[2] or 1) * 100.0) if r[2] else 0.0
                }
                for r in results
            ]

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

    def increment_crawled_count(self, task_type: str, count: int):
        """递增当日抓取数量统计 (Upsert)"""
        stat_date = date.today()
        with session_scope() as session:
            statement = select(SpiderStatisticsModel).where(
                and_(SpiderStatisticsModel.stat_date == stat_date, SpiderStatisticsModel.task_type == task_type)
            )
            stats = session.exec(statement).first()
            
            if stats:
                stats.total_crawled_items = (stats.total_crawled_items or 0) + count
                stats.update_time = datetime.now()
                session.add(stats)
            else:
                new_stats = SpiderStatisticsModel(
                    stat_date=stat_date,
                    task_type=task_type,
                    total_tasks=1,
                    completed_tasks=1,
                    failed_tasks=0,
                    total_crawled_items=count,
                    update_time=datetime.now()
                )
                session.add(new_stats)
            session.commit()

    def save_task_statistics_batch(self, stats_list: List[Dict[str, Any]]):
        """批量保存单次爬取关键词的统计信息"""
        if not stats_list: return
        with session_scope() as session:
            for stats_data in stats_list:
                # 检查是否存在 (同 task_id + keyword + city_code)
                statement = select(TaskStatisticsModel).where(and_(
                    TaskStatisticsModel.task_id == stats_data.get('task_id'),
                    TaskStatisticsModel.keyword == stats_data.get('keyword'),
                    TaskStatisticsModel.city_code == stats_data.get('city_code', '')
                ))
                existing = session.exec(statement).first()
                
                # 转换字段名 (从处理器返回的中文键或标准化后的英文键)
                model_data = {
                    'task_id': stats_data.get('task_id'),
                    'keyword': stats_data.get('关键词') or stats_data.get('keyword'),
                    'city_code': stats_data.get('城市代码') or stats_data.get('city_code'),
                    'city_name': stats_data.get('城市') or stats_data.get('city_name'),
                    'date_range': stats_data.get('时间范围') or stats_data.get('date_range'),
                    'data_type': stats_data.get('数据类型') or stats_data.get('data_type'),
                    'item_count': stats_data.get('数据项数量') or stats_data.get('item_count', 0),
                    'success_count': stats_data.get('成功数量') or stats_data.get('success_count', 0),
                    'fail_count': stats_data.get('失败数量') or stats_data.get('fail_count', 0),
                    'avg_value': stats_data.get('平均值') or stats_data.get('avg_value'),
                    'max_value': stats_data.get('最大值') or stats_data.get('max_value'),
                    'min_value': stats_data.get('最小值') or stats_data.get('min_value'),
                    'sum_value': stats_data.get('总和') or stats_data.get('sum_value'),
                    'extra_data': stats_data.get('extra_data'),
                    'create_time': datetime.now()
                }
                
                if existing:
                    for key, val in model_data.items():
                        setattr(existing, key, val)
                    session.add(existing)
                else:
                    new_stats = TaskStatisticsModel(**model_data)
                    session.add(new_stats)
            session.commit()

    def update_spider_summary(self, task_type: str, total_delta: int = 0, completed_delta: int = 0, failed_delta: int = 0, duration: float = 0, cookie_usage: int = 0, cookie_ban_count: int = 0):
        """更新爬虫总体统计摘要 (任务数、平均时长、Cookie使用情况等)"""
        stat_date = date.today()
        with session_scope() as session:
            statement = select(SpiderStatisticsModel).where(and_(
                SpiderStatisticsModel.stat_date == stat_date,
                SpiderStatisticsModel.task_type == task_type
            ))
            stats = session.exec(statement).first()
            
            if stats:
                old_completed = stats.completed_tasks or 0
                stats.total_tasks = (stats.total_tasks or 0) + total_delta
                stats.completed_tasks = (stats.completed_tasks or 0) + completed_delta
                stats.failed_tasks = (stats.failed_tasks or 0) + failed_delta
                stats.cookie_usage = (stats.cookie_usage or 0) + cookie_usage
                stats.cookie_ban_count = (stats.cookie_ban_count or 0) + cookie_ban_count
                
                # 更新平均执行时间 (加权平均)
                if completed_delta > 0 and duration > 0:
                    new_completed = stats.completed_tasks
                    if new_completed > 0:
                        stats.avg_duration = ((old_completed * (stats.avg_duration or 0)) + (completed_delta * duration)) / new_completed
                
                # Recalculate success rate
                if stats.total_tasks > 0:
                    stats.success_rate = (stats.completed_tasks / stats.total_tasks) * 100.0
                else:
                    stats.success_rate = 0.0

                stats.update_time = datetime.now()
                session.add(stats)
            else:
                success_rate = 0.0
                if (total_delta or 1) > 0:
                     success_rate = (completed_delta / (total_delta or 1)) * 100.0

                stats = SpiderStatisticsModel(
                    stat_date=stat_date,
                    task_type=task_type,
                    total_tasks=total_delta or 1,
                    completed_tasks=completed_delta,
                    failed_tasks=failed_delta,
                    avg_duration=duration if completed_delta > 0 else 0,
                    cookie_usage=cookie_usage,
                    cookie_ban_count=cookie_ban_count,
                    success_rate=success_rate,
                    update_time=datetime.now()
                )
                session.add(stats)
            session.commit()

statistics_repo = StatisticsRepository()
