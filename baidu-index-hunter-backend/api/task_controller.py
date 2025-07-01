"""
任务控制器API
提供任务管理的HTTP接口
"""
import os
import sys
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
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
                'required': ['task_type', 'parameters'],
                'properties': {
                    'task_type': {
                        'type': 'string',
                        'enum': ['search_index', 'feed_index', 'word_graph', 
                                'demographic_attributes', 'interest_profile', 'region_distribution'],
                        'description': '任务类型'
                    },
                    'task_name': {
                        'type': 'string',
                        'description': '任务名称'
                    },
                    'parameters': {
                        'type': 'object',
                        'description': '任务参数，根据任务类型不同而不同'
                    },
                    'created_by': {
                        'type': 'string',
                        'description': '创建者'
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
                    'msg': {'type': 'string', 'example': '任务创建成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'task_id': {'type': 'string', 'example': '20230101120000_abcd1234'}
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
        task_type = data.get('task_type')
        parameters = data.get('parameters')
        
        if not task_type or not parameters:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: task_type 或 parameters"))
        
        # 验证任务类型
        valid_task_types = ['search_index', 'feed_index', 'word_graph', 
                          'demographic_attributes', 'interest_profile', 'region_distribution']
        if task_type not in valid_task_types:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, f"无效的任务类型: {task_type}"))
        
        # 获取可选参数
        task_name = data.get('task_name')
        created_by = data.get('created_by')
        
        # 创建任务
        task_id = task_scheduler.create_task(
            task_type=task_type,
            parameters=parameters,
            task_name=task_name,
            created_by=created_by
        )
        
        return jsonify(ResponseFormatter.success({
            'task_id': task_id
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
                    'msg': {'type': 'string', 'example': '获取任务列表成功'},
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
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        
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
        
        # 处理日期时间格式
        for task in tasks:
            for key, value in task.items():
                if isinstance(value, datetime):
                    task[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            
            # 处理JSON字段
            if 'parameters' in task and task['parameters']:
                try:
                    task['parameters'] = json.loads(task['parameters'])
                except:
                    pass
            
            if 'checkpoint_data' in task and task['checkpoint_data']:
                try:
                    task['checkpoint_data'] = json.loads(task['checkpoint_data'])
                except:
                    pass
            
            if 'output_files' in task and task['output_files']:
                try:
                    task['output_files'] = json.loads(task['output_files'])
                except:
                    pass
        
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
                    'msg': {'type': 'string', 'example': '获取任务详情成功'},
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
                            'checkpoint_data': {'type': 'object'},
                            'output_files': {'type': 'array', 'items': {'type': 'string'}},
                            'created_by': {'type': 'string'}
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
                    'code': {'type': 'integer', 'example': 10404},
                    'msg': {'type': 'string', 'example': '任务不存在'},
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
                    'msg': {'type': 'string', 'example': '任务启动成功'},
                    'data': {'type': 'null'}
                }
            }
        },
        '400': {
            'description': '启动失败',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10400},
                    'msg': {'type': 'string', 'example': '任务启动失败'},
                    'data': {'type': 'null'}
                }
            }
        },
        '404': {
            'description': '任务不存在',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10404},
                    'msg': {'type': 'string', 'example': '任务不存在'},
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
                    'msg': {'type': 'string', 'example': '任务暂停成功'},
                    'data': {'type': 'null'}
                }
            }
        },
        '400': {
            'description': '暂停失败',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10400},
                    'msg': {'type': 'string', 'example': '任务暂停失败'},
                    'data': {'type': 'null'}
                }
            }
        },
        '404': {
            'description': '任务不存在',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10404},
                    'msg': {'type': 'string', 'example': '任务不存在'},
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
            return jsonify(ResponseFormatter.error(ResponseCode.BAD_REQUEST, "任务暂停失败"))
        
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
                    'msg': {'type': 'string', 'example': '任务恢复成功'},
                    'data': {'type': 'null'}
                }
            }
        },
        '400': {
            'description': '恢复失败',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10400},
                    'msg': {'type': 'string', 'example': '任务恢复失败'},
                    'data': {'type': 'null'}
                }
            }
        },
        '404': {
            'description': '任务不存在',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10404},
                    'msg': {'type': 'string', 'example': '任务不存在'},
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
                    'msg': {'type': 'string', 'example': '任务取消成功'},
                    'data': {'type': 'null'}
                }
            }
        },
        '400': {
            'description': '取消失败',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10400},
                    'msg': {'type': 'string', 'example': '任务取消失败'},
                    'data': {'type': 'null'}
                }
            }
        },
        '404': {
            'description': '任务不存在',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10404},
                    'msg': {'type': 'string', 'example': '任务不存在'},
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
            return jsonify(ResponseFormatter.error(ResponseCode.BAD_REQUEST, "任务取消失败"))
        
    except Exception as e:
        log.error(f"取消任务失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"取消任务失败: {str(e)}"))


def register_task_blueprint(app):
    """注册任务蓝图"""
    app.register_blueprint(task_blueprint)
    
    # 启动任务调度器
    task_scheduler.start()