"""
Cookie管理控制器 - 提供Cookie管理的API接口
"""
from flask import Blueprint, request, jsonify
import json
from datetime import datetime, timedelta
from flasgger import swag_from

from cookie_manager.cookie_manager import CookieManager
from constant.respond import ResponseCode, ResponseFormatter

# 创建蓝图
admin_cookie_bp = Blueprint('admin_cookie', __name__, url_prefix='/api/admin/cookie')
cookie_manager = CookieManager()

@admin_cookie_bp.route('/list', methods=['GET'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '获取Cookie列表',
    'description': '获取所有Cookie或根据账号ID过滤',
    'parameters': [
        {
            'name': 'account_id',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': '账号ID，用于过滤指定账号的Cookie'
        },
        {
            'name': 'available_only',
            'in': 'query',
            'type': 'boolean',
            'required': False,
            'default': True,
            'description': '是否只返回可用的Cookie'
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
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'account_id': {'type': 'string'},
                                'cookie_name': {'type': 'string'},
                                'cookie_value': {'type': 'string'},
                                'expire_time': {'type': 'string', 'format': 'date-time'},
                                'is_available': {'type': 'integer'},
                                'is_permanently_banned': {'type': 'integer'},
                                'temp_ban_until': {'type': 'string', 'format': 'date-time'}
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
def list_cookies():
    """获取所有可用的Cookie"""
    try:
        # 获取查询参数
        account_id = request.args.get('account_id')
        available_only = request.args.get('available_only', 'true').lower() == 'true'
        
        if account_id:
            # 获取指定账号的cookie
            cookies = cookie_manager.get_cookies_by_account_id(account_id)
        elif available_only:
            # 获取所有可用的cookie
            cookies = cookie_manager.get_available_cookies()
        else:
            # 获取所有cookie（这个接口需要额外实现）
            cookies = []
            cursor = cookie_manager._get_cursor()
            cursor.execute("SELECT * FROM cookies")
            cookies = cursor.fetchall()
        
        # 转换为可序列化的格式
        result = []
        for cookie in cookies:
            # 处理datetime类型
            cookie_dict = dict(cookie)
            if 'expire_time' in cookie_dict and cookie_dict['expire_time'] is not None:
                cookie_dict['expire_time'] = cookie_dict['expire_time'].strftime('%Y-%m-%d %H:%M:%S')
            if 'temp_ban_until' in cookie_dict and cookie_dict['temp_ban_until'] is not None:
                cookie_dict['temp_ban_until'] = cookie_dict['temp_ban_until'].strftime('%Y-%m-%d %H:%M:%S')
            result.append(cookie_dict)
        
        return jsonify(ResponseFormatter.success(result))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取Cookie列表失败: {str(e)}"))

@admin_cookie_bp.route('/assembled', methods=['GET'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '获取组装后的完整Cookie',
    'description': '获取所有可用账号的完整Cookie字典或根据账号ID列表过滤',
    'parameters': [
        {
            'name': 'account_ids',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': '账号ID列表，多个ID用逗号分隔，用于过滤指定账号的Cookie'
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
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'account_id': {'type': 'string'},
                                'cookie_dict': {'type': 'object'}
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
def get_assembled_cookies():
    """获取组装后的完整Cookie字典"""
    try:
        # 获取查询参数
        account_ids_param = request.args.get('account_ids')
        account_ids = account_ids_param.split(',') if account_ids_param else None
        
        # 获取组装的cookie
        assembled_cookies = cookie_manager.get_assembled_cookies(account_ids)
        
        return jsonify(ResponseFormatter.success(assembled_cookies))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取组装Cookie失败: {str(e)}"))

@admin_cookie_bp.route('/accounts', methods=['GET'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '获取所有可用的账号ID',
    'description': '获取系统中所有可用的账号ID列表',
    'responses': {
        '200': {
            'description': '请求成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'array',
                        'items': {'type': 'string'}
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
def list_accounts():
    """获取所有可用的账号ID"""
    try:
        account_ids = cookie_manager.get_available_account_ids()
        return jsonify(ResponseFormatter.success(account_ids))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取账号列表失败: {str(e)}"))

@admin_cookie_bp.route('/add', methods=['POST'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '添加Cookie',
    'description': '添加新的Cookie到系统',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['account_id', 'cookie_data'],
                'properties': {
                    'account_id': {'type': 'string', 'description': '账号ID'},
                    'cookie_data': {'type': 'object', 'description': 'Cookie数据，可以是字典、JSON字符串或cookie字符串'},
                    'expire_days': {'type': 'integer', 'description': 'Cookie过期天数', 'default': 365}
                }
            }
        }
    ],
    'responses': {
        '200': {
            'description': '添加成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': 'Cookie添加成功'},
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
        }
    }
})
def add_cookie():
    """添加Cookie"""
    try:
        data = request.json
        if not data:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "请求参数不能为空"))
        
        account_id = data.get('account_id')
        cookie_data = data.get('cookie_data')
        expire_days = data.get('expire_days')
        
        if not account_id or not cookie_data:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "账号ID和Cookie数据不能为空"))
        
        # 设置过期时间
        expire_time = None
        if expire_days:
            expire_time = datetime.now() + timedelta(days=expire_days)
        
        # 添加Cookie
        success = cookie_manager.add_cookie(account_id, cookie_data, expire_time)
        
        if success:
            return jsonify(ResponseFormatter.success(None, "Cookie添加成功"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.COOKIE_ERROR, "Cookie添加失败"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"添加Cookie失败: {str(e)}"))

@admin_cookie_bp.route('/delete/<account_id>', methods=['DELETE'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '删除指定账号的所有Cookie',
    'description': '根据账号ID删除所有相关的Cookie记录',
    'parameters': [
        {
            'name': 'account_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '要删除Cookie的账号ID'
        }
    ],
    'responses': {
        '200': {
            'description': '删除成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '成功删除5条Cookie记录'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'deleted_count': {'type': 'integer', 'example': 5}
                        }
                    }
                }
            }
        },
        '404': {
            'description': '未找到记录',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10101},
                    'msg': {'type': 'string', 'example': '未找到指定账号的Cookie记录'},
                    'data': {'type': 'null'}
                }
            }
        }
    }
})
def delete_cookie(account_id):
    """删除指定账号的所有Cookie"""
    try:
        deleted_count = cookie_manager.delete_by_account_id(account_id)
        
        if deleted_count > 0:
            return jsonify(ResponseFormatter.success({"deleted_count": deleted_count}, f"成功删除{deleted_count}条Cookie记录"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "未找到指定账号的Cookie记录"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"删除Cookie失败: {str(e)}"))

@admin_cookie_bp.route('/update/<cookie_id>', methods=['PUT'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '更新指定Cookie',
    'description': '更新指定ID的Cookie记录',
    'parameters': [
        {
            'name': 'cookie_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '要更新的Cookie ID'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'cookie_value': {'type': 'string', 'description': 'Cookie值'},
                    'expire_time': {'type': 'string', 'format': 'date-time', 'description': '过期时间'},
                    'is_available': {'type': 'integer', 'description': '是否可用，0-不可用，1-可用'},
                    'is_permanently_banned': {'type': 'integer', 'description': '是否永久封禁，0-否，1-是'},
                    'temp_ban_until': {'type': 'string', 'format': 'date-time', 'description': '临时封禁截止时间'}
                }
            }
        }
    ],
    'responses': {
        '200': {
            'description': '更新成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': 'Cookie更新成功'},
                    'data': {'type': 'null'}
                }
            }
        },
        '404': {
            'description': '未找到记录',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10101},
                    'msg': {'type': 'string', 'example': '未找到指定的Cookie或更新失败'},
                    'data': {'type': 'null'}
                }
            }
        }
    }
})
def update_cookie(cookie_id):
    """更新指定Cookie"""
    try:
        data = request.json
        if not data:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "请求参数不能为空"))
        
        # 更新Cookie
        success = cookie_manager.update_cookie(cookie_id, data)
        
        if success:
            return jsonify(ResponseFormatter.success(None, "Cookie更新成功"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "未找到指定的Cookie或更新失败"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"更新Cookie失败: {str(e)}"))

@admin_cookie_bp.route('/ban/permanent/<account_id>', methods=['POST'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '永久封禁账号',
    'description': '永久封禁指定账号ID的所有Cookie',
    'parameters': [
        {
            'name': 'account_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '要永久封禁的账号ID'
        }
    ],
    'responses': {
        '200': {
            'description': '封禁成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '成功永久封禁5条Cookie记录'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'banned_count': {'type': 'integer', 'example': 5}
                        }
                    }
                }
            }
        },
        '404': {
            'description': '未找到记录',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10101},
                    'msg': {'type': 'string', 'example': '未找到指定账号的Cookie记录'},
                    'data': {'type': 'null'}
                }
            }
        }
    }
})
def ban_account_permanently(account_id):
    """永久封禁账号"""
    try:
        banned_count = cookie_manager.ban_account_permanently(account_id)
        
        if banned_count > 0:
            return jsonify(ResponseFormatter.success({"banned_count": banned_count}, f"成功永久封禁{banned_count}条Cookie记录"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "未找到指定账号的Cookie记录"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"永久封禁账号失败: {str(e)}"))

@admin_cookie_bp.route('/ban/temporary/<account_id>', methods=['POST'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '临时封禁账号',
    'description': '临时封禁指定账号ID的所有Cookie',
    'parameters': [
        {
            'name': 'account_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '要临时封禁的账号ID'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': False,
            'schema': {
                'type': 'object',
                'properties': {
                    'duration_seconds': {'type': 'integer', 'description': '封禁持续时间(秒)', 'default': 1800}
                }
            }
        }
    ],
    'responses': {
        '200': {
            'description': '封禁成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '成功临时封禁5条Cookie记录，持续1800秒'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'banned_count': {'type': 'integer', 'example': 5},
                            'duration_seconds': {'type': 'integer', 'example': 1800}
                        }
                    }
                }
            }
        }
    }
})
def ban_account_temporarily(account_id):
    """临时封禁账号"""
    try:
        data = request.json or {}
        duration_seconds = data.get('duration_seconds', 1800)  # 默认30分钟
        
        banned_count = cookie_manager.ban_account_temporarily(account_id, duration_seconds)
        
        if banned_count > 0:
            return jsonify(ResponseFormatter.success(
                {"banned_count": banned_count, "duration_seconds": duration_seconds}, 
                f"成功临时封禁{banned_count}条Cookie记录，持续{duration_seconds}秒"
            ))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "未找到指定账号的Cookie记录"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"临时封禁账号失败: {str(e)}"))

@admin_cookie_bp.route('/unban/<account_id>', methods=['POST'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '解封账号',
    'description': '解封指定账号ID的所有Cookie（只解封临时封禁的，永久封禁的不解封）',
    'parameters': [
        {
            'name': 'account_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '要解封的账号ID'
        }
    ],
    'responses': {
        '200': {
            'description': '解封成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '成功解封5条Cookie记录'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'unbanned_count': {'type': 'integer', 'example': 5}
                        }
                    }
                }
            }
        }
    }
})
def unban_account(account_id):
    """解封账号（只解封临时封禁的）"""
    try:
        unbanned_count = cookie_manager.unban_account(account_id)
        
        if unbanned_count > 0:
            return jsonify(ResponseFormatter.success({"unbanned_count": unbanned_count}, f"成功解封{unbanned_count}条Cookie记录"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "未找到可解封的Cookie记录"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"解封账号失败: {str(e)}"))

@admin_cookie_bp.route('/force-unban/<account_id>', methods=['POST'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '强制解封账号',
    'description': '强制解封指定账号ID的所有Cookie（包括永久封禁的）',
    'parameters': [
        {
            'name': 'account_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '要强制解封的账号ID'
        }
    ],
    'responses': {
        '200': {
            'description': '解封成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '成功强制解封5条Cookie记录'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'unbanned_count': {'type': 'integer', 'example': 5}
                        }
                    }
                }
            }
        }
    }
})
def force_unban_account(account_id):
    """强制解封账号（包括永久封禁的）"""
    try:
        unbanned_count = cookie_manager.force_unban_account(account_id)
        
        if unbanned_count > 0:
            return jsonify(ResponseFormatter.success({"unbanned_count": unbanned_count}, f"成功强制解封{unbanned_count}条Cookie记录"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "未找到可解封的Cookie记录"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"强制解封账号失败: {str(e)}"))

@admin_cookie_bp.route('/update-status', methods=['POST'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '更新Cookie状态',
    'description': '检查并更新Cookie状态，将临时封禁过期的Cookie恢复可用',
    'responses': {
        '200': {
            'description': '更新成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '成功更新5条Cookie状态'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'updated_count': {'type': 'integer', 'example': 5}
                        }
                    }
                }
            }
        }
    }
})
def update_cookie_status():
    """检查并更新Cookie状态，将临时封禁过期的Cookie恢复可用"""
    try:
        updated_count = cookie_manager.check_and_update_cookie_status()
        
        return jsonify(ResponseFormatter.success({"updated_count": updated_count}, f"成功更新{updated_count}条Cookie状态"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"更新Cookie状态失败: {str(e)}"))

@admin_cookie_bp.route('/cleanup-expired', methods=['POST'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '清理过期Cookie',
    'description': '清理已过期的Cookie记录',
    'responses': {
        '200': {
            'description': '清理成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '成功清理5条过期Cookie'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'deleted_count': {'type': 'integer', 'example': 5}
                        }
                    }
                }
            }
        }
    }
})
def cleanup_expired_cookies():
    """清理已过期的Cookie"""
    try:
        deleted_count = cookie_manager.cleanup_expired_cookies()
        
        return jsonify(ResponseFormatter.success({"deleted_count": deleted_count}, f"成功清理{deleted_count}条过期Cookie"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"清理过期Cookie失败: {str(e)}"))

@admin_cookie_bp.route('/update-account/<old_account_id>', methods=['PUT'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '更新账号ID',
    'description': '将指定账号ID的所有Cookie记录更新为新的账号ID',
    'parameters': [
        {
            'name': 'old_account_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '原账号ID'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['new_account_id'],
                'properties': {
                    'new_account_id': {'type': 'string', 'description': '新账号ID'}
                }
            }
        }
    ],
    'responses': {
        '200': {
            'description': '更新成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '成功更新5条Cookie记录的账号ID'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'updated_count': {'type': 'integer', 'example': 5}
                        }
                    }
                }
            }
        }
    }
})
def update_account_id(old_account_id):
    """更新账号ID"""
    try:
        data = request.json
        if not data or 'new_account_id' not in data:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "请求参数不能为空且必须包含new_account_id"))
        
        new_account_id = data.get('new_account_id')
        
        updated_count = cookie_manager.update_account_id(old_account_id, new_account_id)
        
        if updated_count > 0:
            return jsonify(ResponseFormatter.success({"updated_count": updated_count}, f"成功更新{updated_count}条Cookie记录的账号ID"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "未找到指定账号的Cookie记录"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"更新账号ID失败: {str(e)}"))

@admin_cookie_bp.route('/test-availability', methods=['POST'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '测试Cookie可用性',
    'description': '测试所有可用Cookie的可用性，并根据测试结果更新Cookie状态',
    'responses': {
        '200': {
            'description': '测试成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': 'Cookie可用性测试完成'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'valid_accounts': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'description': '可用的账号ID列表'
                            },
                            'banned_accounts': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'description': '被封禁的账号ID列表'
                            },
                            'not_login_accounts': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'description': '未登录的账号ID列表'
                            },
                            'total_tested': {'type': 'integer', 'description': '测试的总账号数'},
                            'valid_count': {'type': 'integer', 'description': '可用的账号数'},
                            'banned_count': {'type': 'integer', 'description': '被封禁的账号数'},
                            'not_login_count': {'type': 'integer', 'description': '未登录的账号数'}
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
def test_cookie_availability():
    """测试所有可用Cookie的可用性"""
    try:
        # 调用CookieManager的测试方法
        result = cookie_manager.test_cookies_availability()
        
        return jsonify(ResponseFormatter.success(result, "Cookie可用性测试完成"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"测试Cookie可用性失败: {str(e)}"))

@admin_cookie_bp.route('/test-account-availability/<account_id>', methods=['POST'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '测试单个账号Cookie可用性',
    'description': '测试指定账号ID的Cookie可用性',
    'parameters': [
        {
            'name': 'account_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '要测试的账号ID'
        }
    ],
    'responses': {
        '200': {
            'description': '测试成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': 'Cookie可用性测试完成'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'account_id': {'type': 'string', 'description': '测试的账号ID'},
                            'status': {'type': 'integer', 'description': '测试状态码'},
                            'message': {'type': 'string', 'description': '测试结果消息'},
                            'is_valid': {'type': 'boolean', 'description': '是否有效'},
                            'action_taken': {'type': 'string', 'description': '执行的操作'}
                        }
                    }
                }
            }
        },
        '404': {
            'description': '账号不存在',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10404},
                    'msg': {'type': 'string', 'example': '账号不存在'},
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
def test_account_cookie_availability(account_id):
    """测试单个账号的Cookie可用性"""
    try:
        # 检查账号是否存在
        cookies = cookie_manager.get_cookie_by_account_id(account_id)
        if not cookies:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, f"账号 {account_id} 不存在或没有可用Cookie"))
        
        # 调用CookieManager的测试方法
        result = cookie_manager.test_account_cookie_availability(account_id)
        
        return jsonify(ResponseFormatter.success(result, f"账号 {account_id} Cookie测试完成"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"测试账号 {account_id} Cookie失败: {str(e)}"))

@admin_cookie_bp.route('/available-accounts', methods=['GET'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '获取所有可用账号ID',
    'description': '获取所有可用的账号ID列表',
    'responses': {
        '200': {
            'description': '获取成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '获取可用账号ID成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'account_ids': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'description': '可用的账号ID列表'
                            },
                            'count': {'type': 'integer', 'description': '可用账号数量'}
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
def get_available_account_ids():
    """获取所有可用的账号ID列表"""
    try:
        # 调用CookieManager的方法获取可用账号ID
        account_ids = cookie_manager.get_available_account_ids()
        
        # 返回结果
        result = {
            "account_ids": account_ids,
            "count": len(account_ids)
        }
        
        return jsonify(ResponseFormatter.success(result, "获取可用账号ID成功"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取可用账号ID失败: {str(e)}"))

@admin_cookie_bp.route('/account-cookie/<account_id>', methods=['GET'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '获取单个账号的Cookie信息',
    'description': '获取指定账号ID的Cookie详细信息',
    'parameters': [
        {
            'name': 'account_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '要查询的账号ID'
        }
    ],
    'responses': {
        '200': {
            'description': '获取成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '获取账号Cookie信息成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'account_id': {'type': 'string', 'description': '账号ID'},
                            'cookies': {
                                'type': 'object',
                                'additionalProperties': {'type': 'string'},
                                'description': 'Cookie键值对'
                            },
                            'cookie_count': {'type': 'integer', 'description': 'Cookie数量'},
                            'is_available': {'type': 'boolean', 'description': '是否可用'}
                        }
                    }
                }
            }
        },
        '404': {
            'description': '账号不存在',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10404},
                    'msg': {'type': 'string', 'example': '账号不存在'},
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
def get_account_cookie(account_id):
    """获取指定账号ID的Cookie详细信息"""
    try:
        # 获取账号的cookie记录
        cookies_records = cookie_manager.get_cookies_by_account_id(account_id)
        
        if not cookies_records:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, f"账号 {account_id} 不存在或没有Cookie记录"))
        
        # 获取组装好的cookie字典
        cookie_dict = cookie_manager.get_cookie_by_account_id(account_id)
        
        # 检查是否有可用的cookie
        is_available = cookie_dict is not None
        
        # 如果没有可用cookie但有cookie记录，说明cookie已过期或被禁用
        if not is_available:
            cookie_dict = {}
            for cookie in cookies_records:
                cookie_dict[cookie['cookie_name']] = cookie['cookie_value']
        
        # 返回结果
        result = {
            "account_id": account_id,
            "cookies": cookie_dict,
            "cookie_count": len(cookie_dict),
            "is_available": is_available
        }
        
        return jsonify(ResponseFormatter.success(result, f"获取账号 {account_id} Cookie信息成功"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取账号 {account_id} Cookie信息失败: {str(e)}"))

# 注册蓝图的函数
def register_admin_cookie_blueprint(app):
    """注册Cookie管理API蓝图"""
    app.register_blueprint(admin_cookie_bp)
