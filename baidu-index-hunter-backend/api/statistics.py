"""
统计数据API
"""
import logging
import traceback
from flask import Blueprint, request, jsonify
from db.mysql_manager import MySQLManager

log = logging.getLogger(__name__)

# 创建蓝图
statistics_bp = Blueprint('statistics', __name__)

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
                     WHEN completed_tasks > 0 THEN total_duration / completed_tasks 
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