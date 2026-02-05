"""
配置API模块
提供配置管理的API接口
"""
import json
from flask import Blueprint, request, jsonify
from flasgger import swag_from

from src.services.config_service import config_manager
from src.core.logger import log
from src.core.constants.respond import ResponseCode, ResponseFormatter
from src.api.schemas.config import SetConfigRequest, BatchSetConfigRequest
from src.api.utils.validators import validate_json

# 创建蓝图
config_bp = Blueprint('config', __name__, url_prefix='/api/config')


@config_bp.route('/list', methods=['GET'])
@swag_from({
    'tags': ['系统配置'],
    'summary': '获取配置列表',
    'description': '获取所有配置项或根据前缀过滤',
    'parameters': [
        {
            'name': 'prefix',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': '配置键前缀，用于过滤特定类型的配置项'
        }
    ],
    'responses': {
        '200': {
            'description': '请求成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'additionalProperties': {'type': 'object'}
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
def list_configs():
    """获取所有配置项"""
    try:
        # 获取前缀过滤参数
        prefix = request.args.get('prefix', '')
        
        if prefix:
            configs = config_manager.get_by_prefix(prefix)
        else:
            configs = config_manager.get_all()
        
        # 按键名排序
        sorted_configs = {k: configs[k] for k in sorted(configs.keys())}
        
        return jsonify(ResponseFormatter.success(sorted_configs))
    except Exception as e:
        log.error(f"获取配置列表失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取配置列表失败: {str(e)}")), 500


@config_bp.route('/get/<string:key>', methods=['GET'])
@swag_from({
    'tags': ['系统配置'],
    'summary': '获取单个配置项',
    'description': '根据配置键获取单个配置项的值',
    'parameters': [
        {
            'name': 'key',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '配置键'
        }
    ],
    'responses': {
        '200': {
            'description': '请求成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'key': {'type': 'string', 'example': 'api.host'},
                            'value': {'type': 'string', 'example': '0.0.0.0'}
                        }
                    }
                }
            }
        },
        '404': {
            'description': '配置项不存在',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10101},
                    'msg': {'type': 'string', 'example': '资源不存在'},
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
def get_config(key):
    """获取单个配置项"""
    try:
        value = config_manager.get(key)
        
        if value is None:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, f"配置项 '{key}' 不存在")), 404
        
        return jsonify(ResponseFormatter.success({
            'key': key,
            'value': value
        }))
    except Exception as e:
        log.error(f"获取配置项失败: {key} - {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取配置项失败: {str(e)}")), 500


@config_bp.route('/set', methods=['POST'])
@swag_from({
    'tags': ['系统配置'],
    'summary': '设置配置项',
    'description': '设置单个配置项的值',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['key', 'value'],
                'properties': {
                    'key': {'type': 'string', 'example': 'api.host'},
                    'value': {'type': 'string', 'example': '0.0.0.0'}
                }
            }
        }
    ],
    'responses': {
        '200': {
            'description': '设置成功',
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
@validate_json(SetConfigRequest)
def set_config(validated_data: SetConfigRequest):
    """设置配置项"""
    try:
        key = validated_data.key
        value = validated_data.value
        
        success = config_manager.set(key, value)
        
        if success:
            return jsonify(ResponseFormatter.success(None, f"配置项 '{key}' 设置成功"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"配置项 '{key}' 设置失败")), 500
    except Exception as e:
        log.error(f"设置配置项失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"设置配置项失败: {str(e)}")), 500


@config_bp.route('/delete/<string:key>', methods=['DELETE'])
@swag_from({
    'tags': ['系统配置'],
    'summary': '删除配置项',
    'description': '删除指定的配置项',
    'parameters': [
        {
            'name': 'key',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '要删除的配置键'
        }
    ],
    'responses': {
        '200': {
            'description': '删除成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
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
def delete_config(key):
    """删除配置项"""
    try:
        success = config_manager.delete(key)
        
        if success:
            return jsonify(ResponseFormatter.success(None, f"配置项 '{key}' 删除成功"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"配置项 '{key}' 删除失败")), 500
    except Exception as e:
        log.error(f"删除配置项失败: {key} - {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"删除配置项失败: {str(e)}")), 500


@config_bp.route('/batch_set', methods=['POST'])
@swag_from({
    'tags': ['系统配置'],
    'summary': '批量设置配置项',
    'description': '批量设置多个配置项的值',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'additionalProperties': {
                    'type': 'string'
                },
                'example': {
                    'api.host': '0.0.0.0',
                    'api.port': 5001,
                    'api.debug': True
                }
            }
        }
    ],
    'responses': {
        '200': {
            'description': '设置成功',
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
def batch_set_config():
    """批量设置配置项"""
    try:
        data = request.json
        
        if not data or not isinstance(data, dict):
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "请求体必须是包含配置项的JSON对象")), 400
        
        success_count = 0
        failed_keys = []
        
        for key, value in data.items():
            if config_manager.set(key, value):
                success_count += 1
            else:
                failed_keys.append(key)
        
        if not failed_keys:
            return jsonify(ResponseFormatter.success(None, f"所有配置项设置成功，共 {success_count} 项"))
        else:
            return jsonify(ResponseFormatter.error(
                ResponseCode.SERVER_ERROR, 
                f"部分配置项设置失败: {', '.join(failed_keys)}，成功 {success_count} 项"
            )), 500
    except Exception as e:
        log.error(f"批量设置配置项失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"批量设置配置项失败: {str(e)}")), 500


@config_bp.route('/refresh', methods=['POST'])
@swag_from({
    'tags': ['系统配置'],
    'summary': '刷新配置缓存',
    'description': '从数据库重新加载所有配置项，刷新缓存',
    'responses': {
        '200': {
            'description': '刷新成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
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
def refresh_config():
    """刷新配置缓存"""
    try:
        success = config_manager.refresh_cache()
        
        if success:
            return jsonify(ResponseFormatter.success(None, "配置缓存刷新成功"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, "配置缓存刷新失败")), 500
    except Exception as e:
        log.error(f"刷新配置缓存失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"刷新配置缓存失败: {str(e)}")), 500


@config_bp.route('/init_defaults', methods=['POST'])
@swag_from({
    'tags': ['系统配置'],
    'summary': '初始化默认配置',
    'description': '初始化系统默认配置项',
    'responses': {
        '200': {
            'description': '初始化成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
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
def init_defaults():
    """初始化默认配置"""
    try:
        config_manager.init_default_configs()
        
        return jsonify(ResponseFormatter.success(None, "默认配置初始化成功"))
    except Exception as e:
        log.error(f"初始化默认配置失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"初始化默认配置失败: {str(e)}")), 500 