"""
任务控制器API
提供任务管理的HTTP接口
"""
import os
import sys
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from flasgger import swag_from

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import log
from constant.respond import ResponseCode, ResponseFormatter
from scheduler.task_scheduler import task_scheduler

# 创建蓝图
task_blueprint = Blueprint('task', __name__, url_prefix='/api/task')


@task_blueprint.route('/create', methods=['POST'])
@swag_from({
    'tags': ['任务管理'],
    'summary': '创建爬虫任务',
    'description': '创建一个新的爬虫任务',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['taskType', 'parameters'],
                'properties': {
                    'taskType': {
                        'type': 'string',
                        'enum': ['search_index', 'feed_index', 'word_graph', 
                                'demographic_attributes', 'interest_profile', 'region_distribution'],
                        'description': '任务类型'
                    },
                    'parameters': {
                        'type': 'object',
                        'description': '任务参数，根据任务类型不同而不同'
                    },
                    'priority': {
                        'type': 'integer',
                        'description': '任务优先级，范围1-10，数字越大优先级越高'
                    }
                }
            }
        }
    ],
    'responses': {
        '200': {
            'description': '创建成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'taskId': {'type': 'string', 'example': '20230101120000_abcd1234'}
                        }
                    }
                }
            }
        },
        '400': {
            'description': '参数错误',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10100},
                    'msg': {'type': 'string', 'example': '参数错误'},
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
def create_task():
    """创建爬虫任务"""
    try:
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "请求参数为空"))
        
        # 验证必要参数
        task_type = data.get('taskType')
        parameters = data.get('parameters')
        
        if not task_type or not parameters:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: taskType 或 parameters"))
        
        # 验证任务类型
        valid_task_types = ['search_index', 'feed_index', 'word_graph', 
                          'demographic_attributes', 'interest_profile', 'region_distribution']
        if task_type not in valid_task_types:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, f"无效的任务类型: {task_type}"))
        
        # 获取可选参数
        priority = data.get('priority', 5)  # 默认优先级为5
        
        # 处理搜索指数任务
        if task_type == 'search_index':
            # 验证搜索指数任务的参数
            if 'keywords' not in parameters or not parameters['keywords']:
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: keywords"))
            
            # 验证城市参数
            if 'cities' not in parameters or not parameters['cities']:
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: cities"))
            
            # 处理时间参数
            time_params_count = sum(1 for param in ['days', 'date_ranges', 'year_range'] if param in parameters)
            
            # 处理恢复任务
            resume = parameters.get('resume', False)
            if resume and ('task_id' not in parameters or not parameters['task_id']):
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "恢复任务时必须提供task_id"))
            
            # 准备爬虫参数
            spider_params = {
                'keywords': parameters['keywords'],
                'cities': parameters['cities'],
                'resume': resume
            }
            
            # 添加 kind 参数（数据来源：PC/移动/PC+移动）
            if 'kind' in parameters:
                spider_params['kind'] = parameters['kind']
            
            # 添加时间相关参数
            if 'days' in parameters:
                spider_params['days'] = parameters['days']
            elif 'date_ranges' in parameters:
                spider_params['date_ranges'] = parameters['date_ranges']
            elif 'year_range' in parameters:
                # 将年份字符串转换为整数
                try:
                    start_year = int(parameters['year_range'][0])
                    end_year = int(parameters['year_range'][1])
                    
                    # 直接传递整数年份，让爬虫内部处理日期范围
                    spider_params['year_range'] = [[start_year, end_year]]
                    
                    # 移除下面的代码，因为在爬虫中已经有_process_year_range函数来处理年份范围
                    # 不要在这里生成date_ranges，避免格式问题
                except (ValueError, TypeError, IndexError) as e:
                    return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, f"无效的年份范围: {str(e)}"))
            
            # 添加任务ID（如果是恢复任务）
            if resume and 'task_id' in parameters:
                spider_params['task_id'] = parameters['task_id']
            # log.info(f"111111:{spider_params}")
            
            # 创建任务
            task_id = task_scheduler.create_task(
                task_type=task_type,
                parameters=spider_params,
                task_name=f"搜索指数_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                created_by=None,
                priority=priority
            )
            
            # 如果是恢复任务，设置断点续传数据
            if resume and 'task_id' in parameters:
                # 获取原任务的断点续传数据
                original_task = task_scheduler.get_task(parameters['task_id'])
                if original_task and 'checkpoint_path' in original_task and original_task['checkpoint_path']:
                    # 更新新任务的断点续传数据
                    task_scheduler.update_task_checkpoint(task_id, original_task['checkpoint_path'])
            
            # 启动任务
            task_scheduler.start_task(task_id)
            
            return jsonify(ResponseFormatter.success({
                'taskId': task_id
            }, "搜索指数任务创建成功"))
            
        # 处理资讯指数任务
        elif task_type == 'feed_index':
            # 验证资讯指数任务的参数
            if 'keywords' not in parameters or not parameters['keywords']:
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: keywords"))
            
            # 验证城市参数
            if 'cities' not in parameters or not parameters['cities']:
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: cities"))
            
            # 处理时间参数
            time_params_count = sum(1 for param in ['days', 'date_ranges', 'year_range'] if param in parameters)
            
            # 处理恢复任务
            resume = parameters.get('resume', False)
            if resume and ('task_id' not in parameters or not parameters['task_id']):
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "恢复任务时必须提供task_id"))
            
            # 准备爬虫参数
            spider_params = {
                'keywords': parameters['keywords'],
                'cities': parameters['cities'],
                'resume': resume
            }
            
            # 添加 kind 参数（数据来源：PC/移动/PC+移动）
            if 'kind' in parameters:
                spider_params['kind'] = parameters['kind']
            
            # 添加时间相关参数
            if 'days' in parameters:
                spider_params['days'] = parameters['days']
            elif 'date_ranges' in parameters:
                spider_params['date_ranges'] = parameters['date_ranges']
            elif 'year_range' in parameters:
                # 将年份字符串转换为整数
                try:
                    start_year = int(parameters['year_range'][0])
                    end_year = int(parameters['year_range'][1])
                    
                    # 直接传递整数年份，让爬虫内部处理日期范围
                    spider_params['year_range'] = [[start_year, end_year]]
                    
                    # 移除下面的代码，因为在爬虫中已经有_process_year_range函数来处理年份范围
                    # 不要在这里生成date_ranges，避免格式问题
                except (ValueError, TypeError, IndexError) as e:
                    return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, f"无效的年份范围: {str(e)}"))
            
            # 添加任务ID（如果是恢复任务）
            if resume and 'task_id' in parameters:
                spider_params['task_id'] = parameters['task_id']
            
            # 创建任务
            task_id = task_scheduler.create_task(
                task_type=task_type,
                parameters=spider_params,
                task_name=f"资讯指数_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                created_by=None,
                priority=priority
            )
            
            # 如果是恢复任务，设置断点续传数据
            if resume and 'task_id' in parameters:
                # 获取原任务的断点续传数据
                original_task = task_scheduler.get_task(parameters['task_id'])
                if original_task and 'checkpoint_path' in original_task and original_task['checkpoint_path']:
                    # 更新新任务的断点续传数据
                    task_scheduler.update_task_checkpoint(task_id, original_task['checkpoint_path'])
            
            # 启动任务
            task_scheduler.start_task(task_id)
            
            return jsonify(ResponseFormatter.success({
                'taskId': task_id
            }, "资讯指数任务创建成功"))
        
        # 处理需求图谱任务
        elif task_type == 'word_graph':
            # 验证需求图谱任务的参数
            if 'keywords' not in parameters or not parameters['keywords']:
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: keywords"))
            
            if 'datelists' not in parameters or not parameters['datelists']:
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: datelists"))
            
            # 处理恢复任务
            resume = parameters.get('resume', False)
            if resume and ('task_id' not in parameters or not parameters['task_id']):
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "恢复任务时必须提供task_id"))
            
            # 获取输出格式
            output_format = parameters.get('output_format', 'csv')
            if output_format not in ['csv', 'excel']:
                output_format = 'csv'
            
            # 准备爬虫参数
            spider_params = {
                'keywords': parameters['keywords'],
                'datelists': parameters['datelists'],
                'output_format': output_format,
                'resume': resume
            }
            
            # 添加 kind 参数（数据来源：PC/移动/PC+移动）
            if 'kind' in parameters:
                spider_params['kind'] = parameters['kind']
            
            # 添加任务ID（如果是恢复任务）
            if resume and 'task_id' in parameters:
                spider_params['task_id'] = parameters['task_id']
            
            # 创建任务
            task_id = task_scheduler.create_task(
                task_type=task_type,
                parameters=spider_params,
                task_name=f"需求图谱_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                created_by=None,
                priority=priority
            )
            
            # 如果是恢复任务，设置断点续传数据
            if resume and 'task_id' in parameters:
                # 获取原任务的断点续传数据
                original_task = task_scheduler.get_task(parameters['task_id'])
                if original_task and 'checkpoint_path' in original_task and original_task['checkpoint_path']:
                    # 更新新任务的断点续传数据
                    task_scheduler.update_task_checkpoint(task_id, original_task['checkpoint_path'])
            
            # 启动任务
            task_scheduler.start_task(task_id)
            
            return jsonify(ResponseFormatter.success({
                'taskId': task_id
            }, "需求图谱任务创建成功"))
        
        # 处理人群属性任务
        elif task_type == 'demographic_attributes':
            # 验证人群属性任务的参数
            if 'keywords' not in parameters or not parameters['keywords']:
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: keywords"))
            
            # 处理恢复任务
            resume = parameters.get('resume', False)
            if resume and ('task_id' not in parameters or not parameters['task_id']):
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "恢复任务时必须提供task_id"))
            
            # 获取输出格式
            output_format = parameters.get('output_format', 'csv')
            if output_format not in ['csv', 'excel']:
                output_format = 'csv'
            
            # 获取批处理大小
            batch_size = parameters.get('batch_size', 10)
            if not isinstance(batch_size, int) or batch_size <= 0:
                batch_size = 10
            
            # 准备爬虫参数
            spider_params = {
                'keywords': parameters['keywords'],
                'output_format': output_format,
                'batch_size': batch_size,
                'resume': resume
            }
            
            # 添加 kind 参数（数据来源：PC/移动/PC+移动）
            if 'kind' in parameters:
                spider_params['kind'] = parameters['kind']
            
            # 添加任务ID（如果是恢复任务）
            if resume and 'task_id' in parameters:
                spider_params['task_id'] = parameters['task_id']
            
            # 创建任务
            task_id = task_scheduler.create_task(
                task_type=task_type,
                parameters=spider_params,
                task_name=f"人群属性_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                created_by=None,
                priority=priority
            )
            
            # 如果是恢复任务，设置断点续传数据
            if resume and 'task_id' in parameters:
                # 获取原任务的断点续传数据
                original_task = task_scheduler.get_task(parameters['task_id'])
                if original_task and 'checkpoint_path' in original_task and original_task['checkpoint_path']:
                    # 更新新任务的断点续传数据
                    task_scheduler.update_task_checkpoint(task_id, original_task['checkpoint_path'])
            
            # 启动任务
            task_scheduler.start_task(task_id)
            
            return jsonify(ResponseFormatter.success({
                'taskId': task_id
            }, "人群属性任务创建成功"))
        
        # 处理兴趣分布任务
        elif task_type == 'interest_profile':
            # 验证兴趣分布任务的参数
            if 'keywords' not in parameters or not parameters['keywords']:
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: keywords"))
            
            # 处理恢复任务
            resume = parameters.get('resume', False)
            if resume and ('task_id' not in parameters or not parameters['task_id']):
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "恢复任务时必须提供task_id"))
            
            # 获取输出格式
            output_format = parameters.get('output_format', 'csv')
            if output_format not in ['csv', 'excel']:
                output_format = 'csv'
            
            # 获取批处理大小
            batch_size = parameters.get('batch_size', 10)
            if not isinstance(batch_size, int) or batch_size <= 0:
                batch_size = 10
            
            # 准备爬虫参数
            spider_params = {
                'keywords': parameters['keywords'],
                'output_format': output_format,
                'batch_size': batch_size,
                'resume': resume
            }
            
            # 添加 kind 参数（数据来源：PC/移动/PC+移动）
            if 'kind' in parameters:
                spider_params['kind'] = parameters['kind']
            
            # 添加任务ID（如果是恢复任务）
            if resume and 'task_id' in parameters:
                spider_params['task_id'] = parameters['task_id']
            
            # 创建任务
            task_id = task_scheduler.create_task(
                task_type=task_type,
                parameters=spider_params,
                task_name=f"兴趣分布_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                created_by=None,
                priority=priority
            )
            
            # 如果是恢复任务，设置断点续传数据
            if resume and 'task_id' in parameters:
                # 获取原任务的断点续传数据
                original_task = task_scheduler.get_task(parameters['task_id'])
                if original_task and 'checkpoint_path' in original_task and original_task['checkpoint_path']:
                    # 更新新任务的断点续传数据
                    task_scheduler.update_task_checkpoint(task_id, original_task['checkpoint_path'])
            
            # 启动任务
            task_scheduler.start_task(task_id)
            
            return jsonify(ResponseFormatter.success({
                'taskId': task_id
            }, "兴趣分布任务创建成功"))
        
        # 处理地域分布任务
        elif task_type == 'region_distribution':
            # 验证地域分布任务的参数
            if 'keywords' not in parameters or not parameters['keywords']:
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: keywords"))
            
            if 'regions' not in parameters or not parameters['regions']:
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: regions"))
            
            # 处理时间参数
            time_params_count = sum(1 for param in ['days', 'date_ranges', 'year_range', 'start_date', 'end_date'] if param in parameters)
            
            # 处理恢复任务
            resume = parameters.get('resume', False)
            if resume and ('task_id' not in parameters or not parameters['task_id']):
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "恢复任务时必须提供task_id"))
            
            # 获取输出格式
            output_format = parameters.get('output_format', 'csv')
            if output_format not in ['csv', 'excel']:
                output_format = 'csv'
            
            # 准备爬虫参数
            spider_params = {
                'keywords': parameters['keywords'],
                'regions': parameters['regions'],
                'output_format': output_format,
                'resume': resume
            }
            
            # 添加 kind 参数（数据来源：PC/移动/PC+移动）
            if 'kind' in parameters:
                spider_params['kind'] = parameters['kind']
            
            # 添加时间相关参数
            if 'days' in parameters:
                spider_params['days'] = parameters['days']
            elif 'date_ranges' in parameters:
                spider_params['date_ranges'] = parameters['date_ranges']
            elif 'year_range' in parameters:
                # 将年份字符串转换为整数
                try:
                    start_year = int(parameters['year_range'][0])
                    end_year = int(parameters['year_range'][1])
                    
                    # 直接传递整数年份，让爬虫内部处理日期范围
                    spider_params['year_range'] = [[start_year, end_year]]
                    
                    # 移除下面的代码，因为在爬虫中已经有_process_year_range函数来处理年份范围
                    # 不要在这里生成date_ranges，避免格式问题
                except (ValueError, TypeError, IndexError) as e:
                    return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, f"无效的年份范围: {str(e)}"))
            elif 'start_date' in parameters and 'end_date' in parameters:
                spider_params['start_date'] = parameters['start_date']
                spider_params['end_date'] = parameters['end_date']
            
            # 添加区域级别参数
            if 'regionLevel' in parameters:
                spider_params['region_level'] = parameters['regionLevel']
            
            # 添加任务ID（如果是恢复任务）
            if resume and 'task_id' in parameters:
                spider_params['task_id'] = parameters['task_id']
            
            # 创建任务
            task_id = task_scheduler.create_task(
                task_type=task_type,
                parameters=spider_params,
                task_name=f"地域分布_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                created_by=None,
                priority=priority
            )
            
            # 如果是恢复任务，设置断点续传数据
            if resume and 'task_id' in parameters:
                # 获取原任务的断点续传数据
                original_task = task_scheduler.get_task(parameters['task_id'])
                if original_task and 'checkpoint_path' in original_task and original_task['checkpoint_path']:
                    # 更新新任务的断点续传数据
                    task_scheduler.update_task_checkpoint(task_id, original_task['checkpoint_path'])
            
            # 启动任务
            task_scheduler.start_task(task_id)
            
            return jsonify(ResponseFormatter.success({
                'taskId': task_id
            }, "地域分布任务创建成功"))
        
        # 其他类型任务的处理...
        
        # 默认创建任务
        task_id = task_scheduler.create_task(
            task_type=task_type,
            parameters=parameters,
            task_name=f"{task_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            created_by=None,
            priority=priority
        )
        
        return jsonify(ResponseFormatter.success({
            'taskId': task_id
        }, "任务创建成功"))
        
    except Exception as e:
        log.error(f"创建任务失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"创建任务失败: {str(e)}"))


@task_blueprint.route('/list', methods=['GET'])
@swag_from({
    'tags': ['任务管理'],
    'summary': '获取任务列表',
    'description': '获取任务列表，支持分页和过滤',
    'parameters': [
        {
            'name': 'status',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': '任务状态过滤'
        },
        {
            'name': 'task_type',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': '任务类型过滤'
        },
        {
            'name': 'created_by',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': '创建者过滤'
        },
        {
            'name': 'limit',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'default': 10,
            'description': '每页数量'
        },
        {
            'name': 'offset',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'default': 0,
            'description': '偏移量'
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
                            'total': {'type': 'integer', 'example': 100},
                            'tasks': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'id': {'type': 'integer'},
                                        'task_id': {'type': 'string'},
                                        'task_name': {'type': 'string'},
                                        'task_type': {'type': 'string'},
                                        'status': {'type': 'string'},
                                        'progress': {'type': 'number'},
                                        'create_time': {'type': 'string', 'format': 'date-time'},
                                        'created_by': {'type': 'string'}
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
def list_tasks():
    """获取任务列表"""
    try:
        # 获取查询参数
        status = request.args.get('status')
        task_type = request.args.get('task_type')
        created_by = request.args.get('created_by')
        keyword = request.args.get('keyword')
        
        # 安全地转换整数参数，提供默认值
        try:
            limit = int(request.args.get('limit', 10))
            if limit <= 0:
                limit = 10
        except (ValueError, TypeError):
            limit = 10
            
        try:
            offset = int(request.args.get('offset', 0))
            if offset < 0:
                offset = 0
        except (ValueError, TypeError):
            offset = 0
        
        # log.info(f"查询任务列表: status={status}, task_type={task_type}, created_by={created_by}, keyword={keyword}, limit={limit}, offset={offset}")
        
        # 获取任务列表
        tasks = task_scheduler.list_tasks(
            status=status,
            task_type=task_type,
            created_by=created_by,
            limit=limit,
            offset=offset
        )
        
        # 获取总数
        total = task_scheduler.count_tasks(
            status=status,
            task_type=task_type,
            created_by=created_by
        )
        
        # log.info(f"查询到 {len(tasks)} 条任务记录，总计 {total} 条")
        
        # 处理日期时间格式
        for task in tasks:
            for key, value in task.items():
                if isinstance(value, datetime):
                    task[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            # 处理JSON字段
            if 'parameters' in task and task['parameters']:
                try:
                    if isinstance(task['parameters'], str):
                        # 有些数据库字段可能是双重序列化，先尝试反序列化两次
                        try:
                            task['parameters'] = json.loads(task['parameters'])
                            if isinstance(task['parameters'], str):
                                task['parameters'] = json.loads(task['parameters'])
                        except Exception:
                            # 如果只反序列化一次就能用，则忽略第二次
                            pass
                except Exception as e:
                    log.warning(f"参数解析失败: {e}")

            if 'checkpoint_path' in task and task['checkpoint_path']:
                try:
                    if isinstance(task['checkpoint_path'], str):
                        try:
                            task['checkpoint_path'] = json.loads(task['checkpoint_path'])
                            if isinstance(task['checkpoint_path'], str):
                                task['checkpoint_path'] = json.loads(task['checkpoint_path'])
                        except Exception:
                            pass
                except Exception as e:
                    log.warning(f"检查点路径解析失败: {e}")
            if 'output_files' in task and task['output_files']:
                try:
                    if isinstance(task['output_files'], str):
                        output_files = json.loads(task['output_files'])
                        # 确保输出文件始终是数组格式
                        if not isinstance(output_files, list):
                            output_files = [output_files]
                        task['output_files'] = output_files
                except Exception as e:
                    log.warning(f"输出文件解析失败: {e}")
                    if isinstance(task['output_files'], str):
                        task['output_files'] = [task['output_files']]
        
        return jsonify(ResponseFormatter.success({
            'total': total,
            'tasks': tasks
        }, "获取任务列表成功"))
        
    except Exception as e:
        log.error(f"获取任务列表失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取任务列表失败: {str(e)}"))


@task_blueprint.route('/<task_id>', methods=['GET'])
@swag_from({
    'tags': ['任务管理'],
    'summary': '获取任务详情',
    'description': '获取指定任务的详细信息',
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
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'task_id': {'type': 'string'},
                            'task_name': {'type': 'string'},
                            'task_type': {'type': 'string'},
                            'status': {'type': 'string'},
                            'parameters': {'type': 'object'},
                            'progress': {'type': 'number'},
                            'total_items': {'type': 'integer'},
                            'completed_items': {'type': 'integer'},
                            'failed_items': {'type': 'integer'},
                            'create_time': {'type': 'string', 'format': 'date-time'},
                            'start_time': {'type': 'string', 'format': 'date-time'},
                            'update_time': {'type': 'string', 'format': 'date-time'},
                            'end_time': {'type': 'string', 'format': 'date-time'},
                            'error_message': {'type': 'string'},
                            'checkpoint_path': {'type': 'object'},
                            'output_files': {'type': 'array', 'items': {'type': 'string'}},
                            'created_by': {'type': 'string'},
                            'logs': {'type': 'array', 'items': {'type': 'object'}}
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
def get_task(task_id):
    """获取任务详情"""
    try:
        # 获取任务详情
        task = task_scheduler.get_task(task_id)
        
        if not task:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "任务不存在"))
        
        # 处理日期时间格式
        for key, value in task.items():
            if isinstance(value, datetime):
                task[key] = value.strftime('%Y-%m-%d %H:%M:%S')
        
        # 获取任务日志
        logs = task_scheduler.get_task_logs(task_id, limit=100)
        
        # 处理日志中的日期时间格式
        for log in logs:
            if 'timestamp' in log and isinstance(log['timestamp'], datetime):
                log['timestamp'] = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        # 将日志添加到任务详情中
        task['logs'] = logs
        
        return jsonify(ResponseFormatter.success(task, "获取任务详情成功"))
        
    except Exception as e:
        log.error(f"获取任务详情失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取任务详情失败: {str(e)}"))


@task_blueprint.route('/<task_id>/start', methods=['POST'])
@swag_from({
    'tags': ['任务管理'],
    'summary': '启动任务',
    'description': '启动指定的任务',
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
            'description': '启动成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {'type': 'null'}
                }
            }
        },
        '400': {
            'description': '启动失败',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10100},
                    'msg': {'type': 'string', 'example': '参数错误'},
                    'data': {'type': 'null'}
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
def start_task(task_id):
    """启动任务"""
    try:
        # 检查任务是否存在
        task = task_scheduler.get_task(task_id)
        if not task:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "任务不存在"))
        
        # 启动任务
        result = task_scheduler.start_task(task_id)
        
        if result:
            return jsonify(ResponseFormatter.success(None, "任务启动成功"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.BAD_REQUEST, "任务启动失败"))
        
    except Exception as e:
        log.error(f"启动任务失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"启动任务失败: {str(e)}"))


@task_blueprint.route('/<task_id>/pause', methods=['POST'])
@swag_from({
    'tags': ['任务管理'],
    'summary': '暂停任务',
    'description': '暂停指定的任务',
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
            'description': '暂停成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {'type': 'null'}
                }
            }
        },
        '400': {
            'description': '暂停失败',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10100},
                    'msg': {'type': 'string', 'example': '参数错误'},
                    'data': {'type': 'null'}
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
def pause_task(task_id):
    """暂停任务"""
    try:
        # 检查任务是否存在
        task = task_scheduler.get_task(task_id)
        if not task:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "任务不存在"))
        
        # 暂停任务
        result = task_scheduler.pause_task(task_id)
        
        if result:
            return jsonify(ResponseFormatter.success(None, "任务暂停成功"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "任务暂停失败"))
        
    except Exception as e:
        log.error(f"暂停任务失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"暂停任务失败: {str(e)}"))


@task_blueprint.route('/<task_id>/resume', methods=['POST'])
@swag_from({
    'tags': ['任务管理'],
    'summary': '恢复任务',
    'description': '恢复指定的任务',
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
            'description': '恢复成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {'type': 'null'}
                }
            }
        },
        '400': {
            'description': '恢复失败',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10100},
                    'msg': {'type': 'string', 'example': '参数错误'},
                    'data': {'type': 'null'}
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
def resume_task(task_id):
    """恢复任务"""
    try:
        # 检查任务是否存在
        task = task_scheduler.get_task(task_id)
        if not task:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "任务不存在"))
        
        # 恢复任务
        result = task_scheduler.resume_task(task_id)
        
        if result:
            return jsonify(ResponseFormatter.success(None, "任务恢复成功"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.BAD_REQUEST, "任务恢复失败"))
        
    except Exception as e:
        log.error(f"恢复任务失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"恢复任务失败: {str(e)}"))


@task_blueprint.route('/<task_id>/cancel', methods=['POST'])
@swag_from({
    'tags': ['任务管理'],
    'summary': '取消任务',
    'description': '取消指定的任务',
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
            'description': '取消成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {'type': 'null'}
                }
            }
        },
        '400': {
            'description': '取消失败',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10100},
                    'msg': {'type': 'string', 'example': '参数错误'},
                    'data': {'type': 'null'}
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
def cancel_task(task_id):
    """取消任务"""
    try:
        # 检查任务是否存在
        task = task_scheduler.get_task(task_id)
        if not task:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "任务不存在"))
        
        # 取消任务
        result = task_scheduler.cancel_task(task_id)
        
        if result:
            return jsonify(ResponseFormatter.success(None, "任务取消成功"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "任务取消失败"))
        
    except Exception as e:
        log.error(f"取消任务失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"取消任务失败: {str(e)}"))


@task_blueprint.route('/download', methods=['GET'])
@swag_from({
    'tags': ['任务管理'],
    'summary': '下载任务结果文件',
    'description': '下载指定路径的任务结果文件',
    'parameters': [
        {
            'name': 'filePath',
            'in': 'query',
            'type': 'string',
            'required': True,
            'description': '文件路径'
        }
    ],
    'responses': {
        '200': {
            'description': '文件内容',
            'content': {
                'application/octet-stream': {
                    'schema': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        },
        '400': {
            'description': '参数错误',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10100},
                    'msg': {'type': 'string', 'example': '参数错误'},
                    'data': {'type': 'null'}
                }
            }
        },
        '404': {
            'description': '文件不存在',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10500},
                    'msg': {'type': 'string', 'example': '文件不存在'},
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
def download_file():
    """下载文件"""
    try:
        # 获取文件路径
        file_path = request.args.get('filePath')
        if not file_path:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: filePath"))
        
        # 检查文件是否存在
        if not os.path.isfile(file_path):
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "文件不存在"))
        
        # 提取文件名
        file_name = os.path.basename(file_path)
        
        # 发送文件
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_name,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        log.error(f"下载文件失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"下载文件失败: {str(e)}"))


def register_task_blueprint(app):
    """注册任务蓝图"""
    app.register_blueprint(task_blueprint)
    
    # 启动任务调度器
    task_scheduler.start()