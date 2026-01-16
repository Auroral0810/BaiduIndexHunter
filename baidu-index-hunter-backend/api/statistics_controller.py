"""
统计API控制器
提供任务统计数据的HTTP接口
"""
import os
import sys
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flasgger import swag_from

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import log
from constant.respond import ResponseCode, ResponseFormatter
from db.mysql_manager import MySQLManager

# 创建蓝图
stats_blueprint = Blueprint('statistics', __name__, url_prefix='/api/statistics')
mysql = MySQLManager()


@stats_blueprint.route('/task_summary', methods=['GET'])
@swag_from({
    'tags': ['统计数据'],
    'summary': '获取任务统计摘要',
    'description': '获取系统中任务的统计摘要数据',
    'parameters': [
        {
            'name': 'days',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'default': 7,
            'description': '统计最近几天的数据'
        }
    ],
    'responses': {
        '200': {
            'description': '获取成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'total_tasks': {'type': 'integer'},
                            'completed_tasks': {'type': 'integer'},
                            'running_tasks': {'type': 'integer'},
                            'pending_tasks': {'type': 'integer'},
                            'failed_tasks': {'type': 'integer'},
                            'task_types': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'task_type': {'type': 'string'},
                                        'count': {'type': 'integer'}
                                    }
                                }
                            },
                            'daily_tasks': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'date': {'type': 'string', 'format': 'date'},
                                        'count': {'type': 'integer'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        '500': {
            'description': '服务器错误',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10102},
                    'msg': {'type': 'string', 'example': '服务器内部错误'},
                    'data': {'type': 'null'}
                }
            }
        }
    }
})
def get_task_summary():
    """获取任务统计摘要"""
    try:
        # 获取参数
        days = int(request.args.get('days', 7))
        
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
        # 如果是全部时间，或者时间跨度较大，可以考虑按月统计，这里暂时保持按日
        daily_condition = time_condition
        if not daily_condition:
            # 如果是全部时间，为了图表不过于密集，只取最近365天的数据用于趋势图，或者不做限制
            # 这里不做限制，但在前端展示时可能需要注意
            daily_condition = "" 
        
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
@swag_from({
    'tags': ['统计数据'],
    'summary': '获取任务统计数据',
    'description': '获取指定任务的统计数据',
    'parameters': [
        {
            'name': 'task_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '任务ID'
        }
    ],
    'responses': {
        '200': {
            'description': '获取成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'task_id': {'type': 'string'},
                                'task_type': {'type': 'string'},
                                'keyword': {'type': 'string'},
                                'city_code': {'type': 'string'},
                                'city_name': {'type': 'string'},
                                'data_type': {'type': 'string'},
                                'data_date': {'type': 'string'},
                                'item_count': {'type': 'integer'},
                                'success_count': {'type': 'integer'},
                                'fail_count': {'type': 'integer'},
                                'create_time': {'type': 'string', 'format': 'date-time'},
                                'update_time': {'type': 'string', 'format': 'date-time'}
                            }
                        }
                    }
                }
            }
        },
        '404': {
            'description': '任务不存在',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10500},
                    'msg': {'type': 'string', 'example': '数据不存在'},
                    'data': {'type': 'null'}
                }
            }
        },
        '500': {
            'description': '服务器错误',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10102},
                    'msg': {'type': 'string', 'example': '服务器内部错误'},
                    'data': {'type': 'null'}
                }
            }
        }
    }
})
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
@swag_from({
    'tags': ['统计数据'],
    'summary': '获取爬虫统计数据',
    'description': '获取爬虫执行的统计数据，支持按日期和任务类型筛选',
    'parameters': [
        {
            'name': 'date',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': '日期，格式为YYYY-MM-DD'
        },
        {
            'name': 'task_type',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': '任务类型'
        }
    ],
    'responses': {
        '200': {
            'description': '获取成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'msg': {'type': 'string'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'statistics': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'stat_date': {'type': 'string'},
                                        'task_type': {'type': 'string'},
                                        'total_tasks': {'type': 'integer'},
                                        'completed_tasks': {'type': 'integer'},
                                        'failed_tasks': {'type': 'integer'},
                                        'total_items': {'type': 'integer'},
                                        'total_crawled_items': {'type': 'integer'},
                                        'success_rate': {'type': 'number'},
                                        'avg_duration': {'type': 'number'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        '500': {
            'description': '服务器错误',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'msg': {'type': 'string'},
                    'data': {'type': 'null'}
                }
            }
        }
    }
})
def get_spider_statistics():
    """获取爬虫统计数据"""
    try:
        # 获取查询参数
        date = request.args.get('date')
        task_type = request.args.get('task_type')
        
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
            if 'stat_date' in stat and isinstance(stat['stat_date'], datetime.date):
                stat['stat_date'] = stat['stat_date'].strftime('%Y-%m-%d')
        
        return jsonify(ResponseFormatter.success({'statistics': statistics}, "获取爬虫统计数据成功"))
    
    except Exception as e:
        log.error(f"获取爬虫统计数据失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取爬虫统计数据失败: {str(e)}"))


@stats_blueprint.route('/keyword_statistics', methods=['GET'])
@swag_from({
    'tags': ['统计数据'],
    'summary': '获取关键词统计数据',
    'description': '获取关键词的统计数据',
    'parameters': [
        {
            'name': 'keyword',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': '关键词过滤'
        },
        {
            'name': 'task_type',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': '任务类型过滤'
        },
        {
            'name': 'limit',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'default': 100,
            'description': '返回数量限制'
        }
    ],
    'responses': {
        '200': {
            'description': '获取成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '获取关键词统计数据成功'},
                    'data': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'keyword': {'type': 'string'},
                                'item_count': {'type': 'integer'},
                                'success_count': {'type': 'integer'},
                                'fail_count': {'type': 'integer'},
                                'success_rate': {'type': 'number'}
                            }
                        }
                    }
                }
            }
        }
    }
})
def get_keyword_statistics():
    """获取关键词统计数据"""
    try:
        # 获取参数
        keyword = request.args.get('keyword')
        task_type = request.args.get('task_type')
        limit = int(request.args.get('limit', 100))
        
        # 构建查询条件
        conditions = ["keyword != ''"]  # 排除空关键词
        values = []
        
        if keyword:
            conditions.append("keyword LIKE %s")
            values.append(f"%{keyword}%")
        
        if task_type:
            conditions.append("task_type = %s")
            values.append(task_type)
        
        where_clause = " WHERE " + " AND ".join(conditions)
        
        # 获取关键词统计数据
        query = f"""
            SELECT 
                keyword,
                SUM(item_count) AS item_count,
                SUM(success_count) AS success_count,
                SUM(fail_count) AS fail_count
            FROM task_statistics
            {where_clause}
            GROUP BY keyword
            ORDER BY item_count DESC
            LIMIT %s
        """
        
        values.append(limit)
        keyword_statistics = mysql.fetch_all(query, values)
        
        # 计算成功率
        for item in keyword_statistics:
            total = item['item_count'] if item['item_count'] else 0
            success = item['success_count'] if item['success_count'] else 0
            
            if total > 0:
                item['success_rate'] = round(success / total * 100, 2)
            else:
                item['success_rate'] = 0
        
        return jsonify(ResponseFormatter.success(keyword_statistics, "获取关键词统计数据成功"))
        
    except Exception as e:
        log.error(f"获取关键词统计数据失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取关键词统计数据失败: {str(e)}"))


@stats_blueprint.route('/city_statistics', methods=['GET'])
@swag_from({
    'tags': ['统计数据'],
    'summary': '获取城市统计数据',
    'description': '获取城市的统计数据',
    'parameters': [
        {
            'name': 'city_name',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': '城市名称过滤'
        },
        {
            'name': 'task_type',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': '任务类型过滤'
        },
        {
            'name': 'limit',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'default': 100,
            'description': '返回数量限制'
        }
    ],
    'responses': {
        '200': {
            'description': '获取成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '获取城市统计数据成功'},
                    'data': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'city_code': {'type': 'string'},
                                'city_name': {'type': 'string'},
                                'item_count': {'type': 'integer'},
                                'success_count': {'type': 'integer'},
                                'fail_count': {'type': 'integer'},
                                'success_rate': {'type': 'number'}
                            }
                        }
                    }
                }
            }
        }
    }
})
def get_city_statistics():
    """获取城市统计数据"""
    try:
        # 获取参数
        city_name = request.args.get('city_name')
        task_type = request.args.get('task_type')
        limit = int(request.args.get('limit', 100))
        
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


def register_statistics_blueprint(app):
    """注册统计蓝图"""
    app.register_blueprint(stats_blueprint) 