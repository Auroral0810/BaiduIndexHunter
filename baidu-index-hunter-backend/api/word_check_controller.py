"""
关键词检查API控制器
提供关键词检查的HTTP接口（异步任务模式）
"""
import os
import sys
from datetime import datetime
from flask import Blueprint, request, jsonify
from flasgger import swag_from

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import log
from constant.respond import ResponseCode, ResponseFormatter
from scheduler.task_scheduler import task_scheduler

# 创建蓝图
word_check_blueprint = Blueprint('word_check', __name__, url_prefix='/api/word-check')


@word_check_blueprint.route('/check', methods=['POST'])
@swag_from({
    'tags': ['关键词检查'],
    'summary': '创建关键词检查任务',
    'description': '创建一个异步任务来检查指定的关键词在百度指数中是否存在',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['words'],
                'properties': {
                    'words': {
                        'type': 'array',
                        'items': {
                            'type': 'string'
                        },
                        'description': '要检查的关键词列表'
                    },
                    'task_name': {
                        'type': 'string',
                        'description': '任务名称（可选）'
                    }
                }
            }
        }
    ],
    'responses': {
        '200': {
            'description': '任务创建成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '任务创建成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'task_id': {'type': 'string', 'description': '任务ID'},
                            'task_type': {'type': 'string', 'example': 'word_check'},
                            'status': {'type': 'string', 'example': 'pending'},
                            'total_items': {'type': 'integer', 'description': '总关键词数'}
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
def create_word_check_task():
    """创建关键词检查任务"""
    try:
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "请求参数为空"))
        
        # 验证必要参数
        words = data.get('words')
        if not words:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: words"))
        
        # 验证参数类型
        if not isinstance(words, list):
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "参数 words 必须是数组"))
        
        if len(words) == 0:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "关键词列表不能为空"))
        
        # 任务名称
        task_name = data.get('task_name', f'关键词检查-{len(words)}个词')
        
        # 构建任务参数
        parameters = {
            'keywords': words,
        }
        
        # 创建任务（task_scheduler 会自动生成 task_id 并返回）
        log.info(f"创建关键词检查任务, 关键词数: {len(words)}")
        
        task_id = task_scheduler.create_task(
            task_type='word_check',
            parameters=parameters,
            task_name=task_name,
            priority=5
        )
        
        if task_id:
            return jsonify(ResponseFormatter.success({
                'task_id': task_id,
                'task_name': task_name,
                'task_type': 'word_check',
                'status': 'pending',
                'total_items': len(words),
                'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, "关键词检查任务创建成功"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, "任务创建失败"))
        
    except Exception as e:
        log.error(f"创建关键词检查任务失败: {e}")
        import traceback
        log.error(traceback.format_exc())
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"创建任务失败: {str(e)}"))


@word_check_blueprint.route('/task/<task_id>', methods=['GET'])
@swag_from({
    'tags': ['关键词检查'],
    'summary': '获取关键词检查任务状态',
    'description': '获取指定任务ID的关键词检查任务状态和结果',
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
                            'task_id': {'type': 'string'},
                            'status': {'type': 'string'},
                            'progress': {'type': 'number'},
                            'total_items': {'type': 'integer'},
                            'completed_items': {'type': 'integer'},
                            'failed_items': {'type': 'integer'}
                        }
                    }
                }
            }
        }
    }
})
def get_word_check_task(task_id):
    """获取关键词检查任务状态"""
    try:
        task_info = task_scheduler.get_task_info(task_id)
        
        if not task_info:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, f"任务不存在: {task_id}"))
        
        return jsonify(ResponseFormatter.success(task_info, "获取任务状态成功"))
        
    except Exception as e:
        log.error(f"获取任务状态失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取任务状态失败: {str(e)}"))


@word_check_blueprint.route('/task/<task_id>/start', methods=['POST'])
@swag_from({
    'tags': ['关键词检查'],
    'summary': '启动关键词检查任务',
    'description': '启动一个已创建的关键词检查任务',
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
            'description': '启动成功'
        }
    }
})
def start_word_check_task(task_id):
    """启动关键词检查任务"""
    try:
        result = task_scheduler.start_task(task_id)
        
        if result:
            return jsonify(ResponseFormatter.success({
                'task_id': task_id,
                'status': 'running'
            }, "任务启动成功"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, "任务启动失败"))
        
    except Exception as e:
        log.error(f"启动任务失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"启动任务失败: {str(e)}"))


@word_check_blueprint.route('/task/<task_id>/cancel', methods=['POST'])
@swag_from({
    'tags': ['关键词检查'],
    'summary': '取消关键词检查任务',
    'description': '取消一个正在执行的关键词检查任务',
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
            'description': '取消成功'
        }
    }
})
def cancel_word_check_task(task_id):
    """取消关键词检查任务"""
    try:
        result = task_scheduler.cancel_task(task_id)
        
        if result:
            return jsonify(ResponseFormatter.success({
                'task_id': task_id,
                'status': 'cancelled'
            }, "任务取消成功"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, "任务取消失败"))
        
    except Exception as e:
        log.error(f"取消任务失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"取消任务失败: {str(e)}"))


def register_word_check_blueprint(app):
    """注册关键词检查蓝图"""
    app.register_blueprint(word_check_blueprint)