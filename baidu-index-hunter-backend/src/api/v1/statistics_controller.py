"""
统计API控制器
提供任务统计数据的HTTP接口
"""
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flasgger import swag_from

from src.core.logger import log
from src.core.constants.respond import ResponseCode, ResponseFormatter
from src.data.repositories.mysql_manager import MySQLManager
from src.api.schemas.statistics import (
    TaskSummaryRequest,
    TaskSummaryResponse,
    GetSpiderStatisticsRequest,
    SpiderStatisticsResponse,
    GetKeywordStatisticsRequest,
    KeywordStatisticsResponse,
    GetCityStatisticsRequest,
    CityStatisticsResponse,
    DashboardRequest,
    DashboardDataResponse
)
from src.api.utils.validators import validate_args
from src.api.utils.swagger import create_swagger_spec

# 创建蓝图
stats_blueprint = Blueprint('statistics', __name__, url_prefix='/api/statistics')
mysql = MySQLManager()


# ============== Swagger 规范定义 ==============

TASK_SUMMARY_SPEC = create_swagger_spec(
    request_schema=TaskSummaryRequest,
    response_schema=TaskSummaryResponse,
    summary="获取任务统计摘要",
    description="获取系统中任务的统计摘要数据",
    tags=["统计数据"],
    request_in="query"
)

TASK_STATISTICS_SPEC = create_swagger_spec(
    summary="获取任务统计数据",
    description="获取指定任务的统计数据",
    tags=["统计数据"],
    parameters=[{
        'name': 'task_id',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': '任务ID'
    }]
)

SPIDER_STATISTICS_SPEC = create_swagger_spec(
    request_schema=GetSpiderStatisticsRequest,
    response_schema=SpiderStatisticsResponse,
    summary="获取爬虫统计数据",
    description="获取爬虫执行的统计数据，支持按日期和任务类型筛选",
    tags=["统计数据"],
    request_in="query"
)

KEYWORD_STATISTICS_SPEC = create_swagger_spec(
    request_schema=GetKeywordStatisticsRequest,
    response_schema=KeywordStatisticsResponse,
    summary="获取关键词统计数据",
    description="获取关键词的统计数据",
    tags=["统计数据"],
    request_in="query"
)

CITY_STATISTICS_SPEC = create_swagger_spec(
    request_schema=GetCityStatisticsRequest,
    response_schema=CityStatisticsResponse,
    summary="获取城市统计数据",
    description="获取城市维度的统计数据",
    tags=["统计数据"],
    request_in="query"
)

DASHBOARD_SPEC = create_swagger_spec(
    request_schema=DashboardRequest,
    response_schema=DashboardDataResponse,
    summary="获取大屏展示数据",
    description="获取大屏展示数据，包括任务趋势、成功率、爬取量等",
    tags=["统计数据"],
    request_in="query"
)


# ============== API 端点 ==============

@stats_blueprint.route('/task_summary', methods=['GET'])
@swag_from(TASK_SUMMARY_SPEC)
@validate_args(TaskSummaryRequest)
def get_task_summary(validated_data: TaskSummaryRequest):
    """获取任务统计摘要"""
    try:
        days = validated_data.days
        
        # 构建时间筛选条件
        time_condition = ""
        params = []
        
        if days > 0:
            start_date = datetime.now() - timedelta(days=days)
            time_condition = "WHERE create_time >= %s"
            params.append(start_date)
        
        # 获取总任务数
        query = f"SELECT COUNT(*) AS count FROM spider_tasks {time_condition}"
        result = mysql.fetch_one(query, params)
        total_tasks = result['count'] if result else 0
        
        # 获取不同状态的任务数
        query = f"""
            SELECT status, COUNT(*) AS count 
            FROM spider_tasks 
            {time_condition}
            GROUP BY status
        """
        status_results = mysql.fetch_all(query, params)
        
        # 初始化状态计数
        status_counts = {
            'completed': 0,
            'running': 0,
            'pending': 0,
            'paused': 0,
            'failed': 0,
            'cancelled': 0
        }
        
        # 填充状态计数
        for item in status_results:
            status = item['status']
            if status in status_counts:
                status_counts[status] = item['count']
        
        # 获取任务类型分布
        query = f"""
            SELECT task_type, COUNT(*) AS count 
            FROM spider_tasks 
            {time_condition}
            GROUP BY task_type
        """
        type_results = mysql.fetch_all(query, params)
        
        # 获取每日任务数量
        daily_condition = time_condition
        query = f"""
            SELECT DATE(create_time) AS date, COUNT(*) AS count 
            FROM spider_tasks 
            {daily_condition}
            GROUP BY DATE(create_time)
            ORDER BY date
        """
        daily_results = mysql.fetch_all(query, params)
        
        # 格式化日期
        for item in daily_results:
            if isinstance(item['date'], datetime):
                item['date'] = item['date'].strftime('%Y-%m-%d')
        
        # 构建返回数据
        data = {
            'total_tasks': total_tasks,
            'completed_tasks': status_counts['completed'],
            'running_tasks': status_counts['running'],
            'pending_tasks': status_counts['pending'] + status_counts['paused'],
            'failed_tasks': status_counts['failed'] + status_counts['cancelled'],
            'task_types': type_results,
            'daily_tasks': daily_results
        }
        
        return jsonify(ResponseFormatter.success(data, "获取任务统计摘要成功"))
        
    except Exception as e:
        log.error(f"获取任务统计摘要失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取任务统计摘要失败: {str(e)}"))


@stats_blueprint.route('/task_statistics/<task_id>', methods=['GET'])
@swag_from(TASK_STATISTICS_SPEC)
def get_task_statistics(task_id):
    """获取任务统计数据"""
    try:
        # 检查任务是否存在
        query = "SELECT id FROM spider_tasks WHERE task_id = %s"
        task = mysql.fetch_one(query, (task_id,))
        
        if not task:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "任务不存在"))
        
        # 获取任务统计数据
        query = "SELECT * FROM task_statistics WHERE task_id = %s"
        statistics = mysql.fetch_all(query, (task_id,))
        
        # 处理日期时间格式
        for item in statistics:
            for key, value in item.items():
                if isinstance(value, datetime):
                    item[key] = value.strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify(ResponseFormatter.success(statistics, "获取任务统计数据成功"))
        
    except Exception as e:
        log.error(f"获取任务统计数据失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取任务统计数据失败: {str(e)}"))


@stats_blueprint.route('/spider_statistics', methods=['GET'])
@swag_from(SPIDER_STATISTICS_SPEC)
@validate_args(GetSpiderStatisticsRequest)
def get_spider_statistics(validated_data: GetSpiderStatisticsRequest):
    """获取爬虫统计数据"""
    try:
        date = validated_data.date
        task_type = validated_data.task_type
        
        # 构建查询条件
        conditions = []
        values = []
        
        if date:
            conditions.append("stat_date = %s")
            values.append(date)
        
        if task_type:
            conditions.append("task_type = %s")
            values.append(task_type)
        
        # 构建查询语句
        query = """
            SELECT 
                stat_date, task_type, total_tasks, completed_tasks, 
                failed_tasks, total_items, total_crawled_items, success_rate, avg_duration,
                cookie_usage, cookie_ban_count
            FROM 
                spider_statistics
        """
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY stat_date DESC, task_type ASC"
        
        # 执行查询
        statistics = MySQLManager().fetch_all(query, values)
        
        # 处理日期格式
        for stat in statistics:
            if 'stat_date' in stat and stat['stat_date']:
                if hasattr(stat['stat_date'], 'strftime'):
                    stat['stat_date'] = stat['stat_date'].strftime('%Y-%m-%d')
        
        return jsonify(ResponseFormatter.success({'statistics': statistics}, "获取爬虫统计数据成功"))
    
    except Exception as e:
        log.error(f"获取爬虫统计数据失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取爬虫统计数据失败: {str(e)}"))


@stats_blueprint.route('/keyword_statistics', methods=['GET'])
@swag_from(KEYWORD_STATISTICS_SPEC)
@validate_args(GetKeywordStatisticsRequest)
def get_keyword_statistics(validated_data: GetKeywordStatisticsRequest):
    """获取关键词统计数据"""
    try:
        task_id = validated_data.task_id
        limit = validated_data.limit
        
        # 构建查询条件
        conditions = []
        values = []
        
        if task_id:
            conditions.append("task_id = %s")
            values.append(task_id)
        
        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
        
        # 获取关键词统计
        query = f"""
            SELECT 
                keyword,
                SUM(item_count) AS item_count,
                AVG(CASE WHEN item_count > 0 THEN success_count * 100.0 / item_count ELSE 0 END) AS avg_success_rate
            FROM task_statistics
            {where_clause}
            GROUP BY keyword
            ORDER BY item_count DESC
            LIMIT %s
        """
        
        values.append(limit)
        keyword_statistics = mysql.fetch_all(query, values)
        
        return jsonify(ResponseFormatter.success({
            'keywords': keyword_statistics,
            'total': len(keyword_statistics)
        }, "获取关键词统计数据成功"))
        
    except Exception as e:
        log.error(f"获取关键词统计数据失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取关键词统计数据失败: {str(e)}"))


@stats_blueprint.route('/city_statistics', methods=['GET'])
@swag_from(CITY_STATISTICS_SPEC)
@validate_args(GetCityStatisticsRequest)
def get_city_statistics(validated_data: GetCityStatisticsRequest):
    """获取城市统计数据"""
    try:
        city_name = validated_data.city_name
        task_type = validated_data.task_type
        limit = validated_data.limit
        
        # 构建查询条件
        conditions = ["city_code != ''"]  # 排除空城市代码
        values = []
        
        if city_name:
            conditions.append("city_name LIKE %s")
            values.append(f"%{city_name}%")
        
        if task_type:
            conditions.append("task_type = %s")
            values.append(task_type)
        
        where_clause = " WHERE " + " AND ".join(conditions)
        
        # 获取城市统计数据
        query = f"""
            SELECT 
                city_code,
                city_name,
                SUM(item_count) AS item_count,
                SUM(success_count) AS success_count,
                SUM(fail_count) AS fail_count
            FROM task_statistics
            {where_clause}
            GROUP BY city_code, city_name
            ORDER BY item_count DESC
            LIMIT %s
        """
        
        values.append(limit)
        city_statistics = mysql.fetch_all(query, values)
        
        # 计算成功率
        for item in city_statistics:
            total = item['item_count'] if item['item_count'] else 0
            success = item['success_count'] if item['success_count'] else 0
            
            if total > 0:
                item['success_rate'] = round(success / total * 100, 2)
            else:
                item['success_rate'] = 0
        
        return jsonify(ResponseFormatter.success(city_statistics, "获取城市统计数据成功"))
    except Exception as e:
        log.error(f"获取城市统计数据失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取城市统计数据失败: {str(e)}"))


@stats_blueprint.route('/dashboard', methods=['GET'])
@swag_from(DASHBOARD_SPEC)
@validate_args(DashboardRequest)
def get_dashboard_data(validated_data: DashboardRequest):
    """获取大屏展示数据"""
    try:
        days = validated_data.days
        start_date_str = validated_data.start_date
        end_date_str = validated_data.end_date
        
        # 计算日期范围
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=30)
        elif days == -1:
            end_date = datetime.now().date()
            start_date = datetime(2000, 1, 1).date()
        else:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
        
        # 获取任务类型列表
        task_types_query = "SELECT DISTINCT task_type FROM spider_statistics ORDER BY task_type"
        task_types_result = mysql.fetch_all(task_types_query)
        task_types = [item['task_type'] for item in task_types_result]
        
        # 1. 获取总体统计数据
        overall_query = """
            SELECT 
                SUM(total_tasks) as total_tasks, SUM(completed_tasks) as completed_tasks,
                SUM(failed_tasks) as failed_tasks, SUM(total_items) as total_items,
                SUM(total_crawled_items) as total_crawled_items,
                CASE WHEN SUM(total_tasks) > 0 THEN (SUM(completed_tasks) / SUM(total_tasks)) * 100 ELSE 0 END as success_rate,
                CASE WHEN SUM(completed_tasks) > 0 THEN SUM(completed_tasks * avg_duration) / SUM(completed_tasks) ELSE 0 END as avg_duration
            FROM spider_statistics WHERE stat_date BETWEEN %s AND %s
        """
        overall_stats = mysql.fetch_one(overall_query, (start_date, end_date))
        
        # 3. 获取每日统计趋势数据
        daily_trend_query = """
            SELECT stat_date, SUM(total_tasks) as total_tasks, SUM(completed_tasks) as completed_tasks,
                   SUM(failed_tasks) as failed_tasks, SUM(total_items) as total_items,
                   SUM(total_crawled_items) as total_crawled_items
            FROM spider_statistics WHERE stat_date BETWEEN %s AND %s
            GROUP BY stat_date ORDER BY stat_date
        """
        daily_trend = mysql.fetch_all(daily_trend_query, (start_date, end_date))
        for item in daily_trend:
            if 'stat_date' in item and item['stat_date']:
                item['stat_date'] = item['stat_date'].strftime('%Y-%m-%d')
        
        return jsonify(ResponseFormatter.success({
            'task_types': task_types,
            'overall': overall_stats,
            'daily_trend': daily_trend
        }))
    except Exception as e:
        log.error(f"获取大屏数据失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取大屏数据失败: {str(e)}"))


def register_statistics_blueprint(app):
    """注册统计蓝图"""
    app.register_blueprint(stats_blueprint)