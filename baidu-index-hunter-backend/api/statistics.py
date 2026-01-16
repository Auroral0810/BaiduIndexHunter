"""
统计数据API
"""
import logging
import traceback
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from db.mysql_manager import MySQLManager

log = logging.getLogger(__name__)

# 创建蓝图
statistics_bp = Blueprint('statistics', __name__, url_prefix='/api/statistics')

@statistics_bp.route('/spider_statistics', methods=['GET'])
def get_spider_statistics():
    """获取爬虫统计数据"""
    try:
        # 获取查询参数
        date = request.args.get('date')
        task_type = request.args.get('taskType')
        
        # 构建查询条件
        conditions = []
        params = []
        
        if date:
            conditions.append("stat_date = %s")
            params.append(date)
        
        if task_type:
            conditions.append("task_type = %s")
            params.append(task_type)
        
        # 构建SQL查询
        query = """
            SELECT id, stat_date, task_type, total_tasks, completed_tasks, failed_tasks, 
                   total_items, total_crawled_items, create_time, update_time,
                   CASE 
                     WHEN total_tasks > 0 THEN (completed_tasks / total_tasks) * 100 
                     ELSE 0 
                   END AS success_rate,
                   CASE 
                     WHEN completed_tasks > 0 THEN avg_duration 
                     ELSE 0 
                   END AS avg_duration
            FROM spider_statistics
        """
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY stat_date DESC, task_type"
        
        # 执行查询
        mysql = MySQLManager()
        statistics = mysql.fetch_all(query, params if params else None)
        
        # 转换日期时间格式
        for stat in statistics:
            if 'stat_date' in stat and stat['stat_date']:
                stat['stat_date'] = stat['stat_date'].strftime('%Y-%m-%d')
            if 'create_time' in stat and stat['create_time']:
                stat['create_time'] = stat['create_time'].strftime('%Y-%m-%d %H:%M:%S')
            if 'update_time' in stat and stat['update_time']:
                stat['update_time'] = stat['update_time'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'code': 10000,
            'msg': 'success',
            'data': {
                'statistics': statistics
            }
        })
    except Exception as e:
        log.error(f"获取爬虫统计数据失败: {e}")
        log.error(traceback.format_exc())
        return jsonify({
            'code': 50000,
            'msg': f"获取爬虫统计数据失败: {str(e)}"
        })

@statistics_bp.route('/task_statistics', methods=['GET'])
def get_task_statistics():
    """获取任务统计数据"""
    try:
        # 获取查询参数
        task_type = request.args.get('taskType')
        keyword = request.args.get('keyword')
        date_start = request.args.get('dateStart')
        date_end = request.args.get('dateEnd')
        
        # 构建查询条件
        conditions = []
        params = []
        
        if task_type:
            conditions.append("task_type = %s")
            params.append(task_type)
        
        if keyword:
            conditions.append("keyword LIKE %s")
            params.append(f"%{keyword}%")
        
        if date_start:
            conditions.append("DATE(data_date) >= %s")
            params.append(date_start)
        
        if date_end:
            conditions.append("DATE(data_date) <= %s")
            params.append(date_end)
        
        # 构建SQL查询
        query = """
            SELECT 
                id, task_id, task_type, keyword, city_code, city_name, 
                data_type, data_date, item_count, success_count, fail_count, 
                create_time, update_time
            FROM task_statistics
        """
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY data_date DESC, keyword"
        
        # 执行查询
        mysql = MySQLManager()
        statistics = mysql.fetch_all(query, params if params else None)
        
        # 转换日期时间格式
        for stat in statistics:
            if 'data_date' in stat and stat['data_date']:
                stat['data_date'] = stat['data_date'].strftime('%Y-%m-%d')
            if 'create_time' in stat and stat['create_time']:
                stat['create_time'] = stat['create_time'].strftime('%Y-%m-%d %H:%M:%S')
            if 'update_time' in stat and stat['update_time']:
                stat['update_time'] = stat['update_time'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'code': 10000,
            'msg': 'success',
            'data': {
                'statistics': statistics
            }
        })
    except Exception as e:
        log.error(f"获取任务统计数据失败: {e}")
        log.error(traceback.format_exc())
        return jsonify({
            'code': 50000,
            'msg': f"获取任务统计数据失败: {str(e)}"
        })

@statistics_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    """获取大屏展示数据"""
    try:
        # 获取查询参数
        days = request.args.get('days', default=30, type=int)
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # 计算日期范围
        if start_date_str and end_date_str:
            # 如果提供了具体的开始和结束日期
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                # 日期格式错误，回退到默认逻辑
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=30)
        elif days == -1:
            # 全部时间：设置一个很久以前的开始时间
            end_date = datetime.now().date()
            start_date = datetime(2000, 1, 1).date()
        else:
            # 正常按天数计算
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
        
        mysql = MySQLManager()
        
        # 获取任务类型列表
        task_types_query = """
            SELECT DISTINCT task_type FROM spider_statistics
            ORDER BY task_type
        """
        task_types_result = mysql.fetch_all(task_types_query)
        task_types = [item['task_type'] for item in task_types_result]
        
        # 1. 获取总体统计数据
        overall_query = """
            SELECT 
                SUM(total_tasks) as total_tasks,
                SUM(completed_tasks) as completed_tasks,
                SUM(failed_tasks) as failed_tasks,
                SUM(total_items) as total_items,
                SUM(total_crawled_items) as total_crawled_items,
                CASE 
                    WHEN SUM(total_tasks) > 0 THEN (SUM(completed_tasks) / SUM(total_tasks)) * 100
                    ELSE 0
                END as success_rate,
                CASE 
                    WHEN SUM(completed_tasks) > 0 THEN SUM(completed_tasks * avg_duration) / SUM(completed_tasks)
                    ELSE 0
                END as avg_duration
            FROM spider_statistics
            WHERE stat_date BETWEEN %s AND %s
        """
        overall_stats = mysql.fetch_one(overall_query, (start_date, end_date))
        
        # 2. 获取按任务类型分组的统计数据
        task_type_query = """
            SELECT 
                task_type,
                SUM(total_tasks) as total_tasks,
                SUM(completed_tasks) as completed_tasks,
                SUM(failed_tasks) as failed_tasks,
                SUM(total_items) as total_items,
                SUM(total_crawled_items) as total_crawled_items,
                CASE 
                    WHEN SUM(total_tasks) > 0 THEN (SUM(completed_tasks) / SUM(total_tasks)) * 100
                    ELSE 0
                END as success_rate,
                CASE 
                    WHEN SUM(completed_tasks) > 0 THEN SUM(completed_tasks * avg_duration) / SUM(completed_tasks)
                    ELSE 0
                END as avg_duration
            FROM spider_statistics
            WHERE stat_date BETWEEN %s AND %s
            GROUP BY task_type
            ORDER BY task_type
        """
        task_type_stats = mysql.fetch_all(task_type_query, (start_date, end_date))
        
        # 3. 获取每日统计趋势数据
        daily_trend_query = """
            SELECT 
                stat_date,
                SUM(total_tasks) as total_tasks,
                SUM(completed_tasks) as completed_tasks,
                SUM(failed_tasks) as failed_tasks,
                SUM(total_items) as total_items,
                SUM(total_crawled_items) as total_crawled_items
            FROM spider_statistics
            WHERE stat_date BETWEEN %s AND %s
            GROUP BY stat_date
            ORDER BY stat_date
        """
        daily_trend = mysql.fetch_all(daily_trend_query, (start_date, end_date))
        
        # 转换日期格式
        for item in daily_trend:
            if 'stat_date' in item and item['stat_date']:
                item['stat_date'] = item['stat_date'].strftime('%Y-%m-%d')
        
        # 4. 获取每种任务类型的每日统计趋势
        task_type_trends = {}
        for task_type in task_types:
            task_trend_query = """
                SELECT 
                    stat_date,
                    total_tasks,
                    completed_tasks,
                    failed_tasks,
                    total_items,
                    total_crawled_items
                FROM spider_statistics
                WHERE stat_date BETWEEN %s AND %s AND task_type = %s
                ORDER BY stat_date
            """
            trend_data = mysql.fetch_all(task_trend_query, (start_date, end_date, task_type))
            
            # 转换日期格式
            for item in trend_data:
                if 'stat_date' in item and item['stat_date']:
                    item['stat_date'] = item['stat_date'].strftime('%Y-%m-%d')
            
            task_type_trends[task_type] = trend_data
        
        # 5. 获取任务成功率对比
        success_rate_query = """
            SELECT 
                task_type,
                CASE 
                    WHEN SUM(total_tasks) > 0 THEN (SUM(completed_tasks) / SUM(total_tasks)) * 100
                    ELSE 0
                END as success_rate
            FROM spider_statistics
            WHERE stat_date BETWEEN %s AND %s
            GROUP BY task_type
            ORDER BY task_type
        """
        success_rate_comparison = mysql.fetch_all(success_rate_query, (start_date, end_date))
        
        # 6. 获取平均执行时间对比
        avg_duration_query = """
            SELECT 
                task_type,
                CASE 
                    WHEN SUM(completed_tasks) > 0 THEN SUM(completed_tasks * avg_duration) / SUM(completed_tasks)
                    ELSE 0
                END as avg_duration
            FROM spider_statistics
            WHERE stat_date BETWEEN %s AND %s
            GROUP BY task_type
            ORDER BY task_type
        """
        avg_duration_comparison = mysql.fetch_all(avg_duration_query, (start_date, end_date))
        
        # 7. 获取数据爬取量对比
        data_volume_query = """
            SELECT 
                task_type,
                SUM(total_crawled_items) as total_crawled_items
            FROM spider_statistics
            WHERE stat_date BETWEEN %s AND %s
            GROUP BY task_type
            ORDER BY task_type
        """
        data_volume_comparison = mysql.fetch_all(data_volume_query, (start_date, end_date))
        
        return jsonify({
            'code': 10000,
            'msg': 'success',
            'data': {
                'task_types': task_types,
                'overall': overall_stats,
                'by_task_type': task_type_stats,
                'daily_trend': daily_trend,
                'task_type_trends': task_type_trends,
                'success_rate_comparison': success_rate_comparison,
                'avg_duration_comparison': avg_duration_comparison,
                'data_volume_comparison': data_volume_comparison
            }
        })
    except Exception as e:
        log.error(f"获取大屏数据失败: {e}")
        log.error(traceback.format_exc())
        return jsonify({
            'code': 50000,
            'msg': f"获取大屏数据失败: {str(e)}"
        }) 
        
def register_statistics_bp(app):
    """注册统计蓝图"""
    app.register_blueprint(statistics_bp) 