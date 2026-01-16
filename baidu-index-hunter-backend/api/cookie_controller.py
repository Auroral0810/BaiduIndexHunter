"""
Cookie管理控制器 - 提供Cookie管理的API接口
"""
from flask import Blueprint, request, jsonify
import json
from datetime import datetime, timedelta
from flasgger import swag_from
import pymysql
import traceback
import functools

from cookie_manager.cookie_manager import CookieManager
from constant.respond import ResponseCode, ResponseFormatter
from config.settings import MYSQL_CONFIG
from utils.logger import log

# 创建蓝图
admin_cookie_bp = Blueprint('admin_cookie', __name__, url_prefix='/api/admin/cookie')

# 使用函数获取cookie_manager实例，而不是全局变量
def get_cookie_manager():
    """获取CookieManager实例，确保每个请求使用新的连接"""
    return CookieManager()

def with_cookie_manager(func):
    """装饰器：为API函数提供cookie_manager实例，并确保正确关闭连接"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        cookie_manager = None
        try:
            cookie_manager = get_cookie_manager()
            return func(cookie_manager, *args, **kwargs)
        except Exception as e:
            log.error(f"{func.__name__}失败: {str(e)}\n{traceback.format_exc()}")
            return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"{func.__name__}失败: {str(e)}"))
        finally:
            if cookie_manager:
                cookie_manager.close()
    return wrapper

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
            'name': 'status',
            'in': 'query',
            'type': 'string',
            'required': False,
            'enum': ['available', 'temp_banned', 'perm_banned', 'expired'],
            'description': 'Cookie状态筛选'
        },
        {
            'name': 'available_only',
            'in': 'query',
            'type': 'boolean',
            'required': False,
            'default': True,
            'description': '是否只返回可用的Cookie'
        },
        {
            'name': 'page',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'default': 1,
            'description': '页码，从1开始'
        },
        {
            'name': 'limit',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'default': 10,
            'description': '每页记录数'
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
                                'cookies': {'type': 'object'},
                                'expire_time': {'type': 'string', 'format': 'date-time'},
                                'is_available': {'type': 'integer'},
                                'is_permanently_banned': {'type': 'integer'},
                                'temp_ban_until': {'type': 'string', 'format': 'date-time'}
                            }
                        }
                    },
                    'total': {'type': 'integer', 'description': '总记录数'}
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
@with_cookie_manager
def list_cookies(cookie_manager):
    """获取所有Cookie，按账号ID组装"""
    try:
        # 获取查询参数
        account_id = request.args.get('account_id')
        available_only = request.args.get('available_only', 'false').lower() == 'true'
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        
        cursor = cookie_manager._get_cursor()
        
        # 首先获取所有账号ID
        if account_id:
            # 获取指定账号的cookie
            cursor.execute("SELECT DISTINCT account_id FROM cookies WHERE account_id = %s", (account_id,))
        elif status:
            # 根据状态过滤
            if status == 'perm_banned':
                cursor.execute("SELECT DISTINCT account_id FROM cookies WHERE is_permanently_banned = 1")
            elif status == 'temp_banned':
                cursor.execute("""
                    SELECT DISTINCT account_id FROM cookies 
                    WHERE temp_ban_until IS NOT NULL AND temp_ban_until > NOW()
                    AND is_permanently_banned = 0
                """)
            elif status == 'expired':
                cursor.execute("SELECT DISTINCT account_id FROM cookies WHERE expire_time IS NOT NULL AND expire_time < NOW()")
            elif status == 'available':
                cursor.execute("""
                    SELECT DISTINCT account_id FROM cookies 
                    WHERE is_available = 1 
                    AND (expire_time IS NULL OR expire_time >= NOW())
                    AND (temp_ban_until IS NULL OR temp_ban_until <= NOW())
                    AND is_permanently_banned = 0
                """)
            else:
                # 未知状态，返回所有
                cursor.execute("SELECT DISTINCT account_id FROM cookies")
        elif available_only:
            # 获取所有可用的账号ID
            cursor.execute("""
                SELECT DISTINCT account_id FROM cookies 
                WHERE is_available = 1 
                AND (expire_time IS NULL OR expire_time > NOW())
                AND (temp_ban_until IS NULL OR temp_ban_until < NOW())
                AND is_permanently_banned = 0
            """)
        else:
            # 获取所有账号ID
            cursor.execute("SELECT DISTINCT account_id FROM cookies")
        
        all_account_ids = [row['account_id'] for row in cursor.fetchall()]
        total_accounts = len(all_account_ids)
        
        # 计算分页
        offset = (page - 1) * limit
        paginated_account_ids = all_account_ids[offset:offset+limit] if offset < total_accounts else []
        
        # 获取分页后的账号的所有Cookie
        result = []
        for acc_id in paginated_account_ids:
            # 获取该账号的所有cookie
            cursor.execute("SELECT * FROM cookies WHERE account_id = %s", (acc_id,))
            cookies = cursor.fetchall()
            
            if not cookies:
                continue
                
            # 组装cookie字典
            cookie_dict = {}
            is_available = True
            is_permanently_banned = False
            temp_ban_until = None
            expire_time = None
            
            for cookie in cookies:
                cookie_dict[cookie['cookie_name']] = cookie['cookie_value']
                
                # 如果任一cookie不可用或被永久封禁，则整个账号被视为不可用
                if not cookie['is_available']:
                    is_available = False
                if cookie.get('is_permanently_banned'):
                    is_permanently_banned = True
                
                # 记录临时封禁时间（取最大值）
                if cookie.get('temp_ban_until'):
                    if temp_ban_until is None or cookie['temp_ban_until'] > temp_ban_until:
                        temp_ban_until = cookie['temp_ban_until']
                
                # 记录过期时间（取最小值，即最早过期的时间）
                if cookie.get('expire_time'):
                    if expire_time is None or cookie['expire_time'] < expire_time:
                        expire_time = cookie['expire_time']
            
            # 处理日期格式
            if expire_time:
                expire_time = expire_time.strftime('%Y-%m-%d %H:%M:%S')
            if temp_ban_until:
                temp_ban_until = temp_ban_until.strftime('%Y-%m-%d %H:%M:%S')
            
            # 添加到结果列表
            result_item = {
                'account_id': acc_id,
                'cookies': cookie_dict,
                'cookie_count': len(cookie_dict),
                'is_available': 1 if is_available else 0,
                'is_permanently_banned': 1 if is_permanently_banned else 0,
                'temp_ban_until': temp_ban_until,
                'expire_time': expire_time
            }
            
            # 二次过滤：确保聚合后的结果符合状态筛选条件
            if status:
                if status == 'perm_banned' and result_item['is_permanently_banned'] != 1:
                    continue
                elif status == 'temp_banned' and not (result_item['temp_ban_until'] and result_item['is_permanently_banned'] == 0):
                    continue
                elif status == 'available' and result_item['is_available'] != 1:
                    continue
                elif status == 'expired' and not (result_item['expire_time'] and datetime.strptime(result_item['expire_time'], '%Y-%m-%d %H:%M:%S') < datetime.now()):
                    continue
            
            result.append(result_item)
        
        # 返回结果，包含分页信息
        response_data = {
            'code': 10000,
            'msg': '请求成功',
            'data': result,
            'total': total_accounts,
            'page': page,
            'limit': limit
        }
        
        return jsonify(response_data)
    except Exception as e:
        log.error(f"获取Cookie列表失败: {str(e)}\n{traceback.format_exc()}")
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
@with_cookie_manager
def get_assembled_cookies(cookie_manager):
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
@with_cookie_manager
def list_accounts(cookie_manager):
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
@with_cookie_manager
def add_cookie(cookie_manager):
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
@with_cookie_manager
def delete_cookie(cookie_manager,account_id):
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
@with_cookie_manager
def update_cookie(cookie_manager,account_id):
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
@with_cookie_manager
def ban_account_permanently(cookie_manager,account_id):
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
@with_cookie_manager
def ban_account_temporarily(cookie_manager,account_id):
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
@with_cookie_manager
def unban_account(cookie_manager,account_id):
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
@with_cookie_manager
def force_unban_account(cookie_manager,account_id):
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
@with_cookie_manager
def update_cookie_status(cookie_manager):
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
@with_cookie_manager
def cleanup_expired_cookies(cookie_manager):
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
@with_cookie_manager
def update_account_id(cookie_manager,old_account_id):
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
@with_cookie_manager
def test_cookie_availability(cookie_manager):
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
@with_cookie_manager
def test_account_cookie_availability(cookie_manager,account_id):
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
@with_cookie_manager
def get_available_account_ids(cookie_manager):
    """获取所有可用的账号ID列表"""
    try:
        # 直接使用SQL查询获取可用账号，而不是调用CookieManager方法
        cursor = cookie_manager._get_cursor()
        cursor.execute("""
            SELECT DISTINCT account_id FROM cookies 
            WHERE is_available = 1 
            AND (expire_time IS NULL OR expire_time > NOW())
            AND (temp_ban_until IS NULL OR temp_ban_until < NOW())
            AND is_permanently_banned = 0
        """)
        results = cursor.fetchall()
        account_ids = [item['account_id'] for item in results]
        
        # 返回结果
        result = {
            "account_ids": account_ids,
            "count": len(account_ids)
        }
        
        return jsonify(ResponseFormatter.success(result, "获取可用账号ID成功"))
    except Exception as e:
        log.error(f"获取可用账号ID失败: {str(e)}\n{traceback.format_exc()}")
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
@with_cookie_manager
def get_account_cookie(cookie_manager,account_id):
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

@admin_cookie_bp.route('/pool-status', methods=['GET'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': 'Cookie池状态',
    'description': '获取Cookie池的总体状态，包括总数、可用数、临时封禁数和永久封禁数',
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
                            'total': {'type': 'integer', 'description': 'Cookie账号总数'},
                            'available': {'type': 'integer', 'description': '可用Cookie账号数量'},
                            'temp_banned': {'type': 'integer', 'description': '临时封禁Cookie账号数量'},
                            'perm_banned': {'type': 'integer', 'description': '永久封禁Cookie账号数量'}
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
@with_cookie_manager
def get_pool_status(cookie_manager):
    """获取Cookie池状态"""
    try:
        cursor = cookie_manager._get_cursor()
        
        # 获取总账号数
        cursor.execute("SELECT COUNT(DISTINCT account_id) as total FROM cookies")
        total = cursor.fetchone()['total']
        
        # 获取可用账号数
        cursor.execute("""
            SELECT COUNT(DISTINCT account_id) as available FROM cookies 
            WHERE is_available = 1 
            AND (expire_time IS NULL OR expire_time > NOW())
            AND (temp_ban_until IS NULL OR temp_ban_until < NOW())
            AND is_permanently_banned = 0
        """)
        available = cursor.fetchone()['available']
        
        # 获取临时封禁账号数
        cursor.execute("""
            SELECT COUNT(DISTINCT account_id) as temp_banned FROM cookies 
            WHERE temp_ban_until IS NOT NULL AND temp_ban_until > NOW()
            AND is_permanently_banned = 0
        """)
        temp_banned = cursor.fetchone()['temp_banned']
        
        # 获取永久封禁账号数
        cursor.execute("SELECT COUNT(DISTINCT account_id) as perm_banned FROM cookies WHERE is_permanently_banned = 1")
        perm_banned = cursor.fetchone()['perm_banned']
        
        result = {
            "total": total,
            "available": available,
            "temp_banned": temp_banned,
            "perm_banned": perm_banned
        }
        
        return jsonify(ResponseFormatter.success(result))
    except Exception as e:
        log.error(f"获取Cookie池状态失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取Cookie池状态失败: {str(e)}"))

@admin_cookie_bp.route('/banned-accounts', methods=['GET'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '获取被封禁的账号',
    'description': '获取所有被临时封禁和永久封禁的账号列表',
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
                            'temp_banned': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'account_id': {'type': 'string'},
                                        'temp_ban_until': {'type': 'string', 'format': 'date-time'},
                                        'remaining_seconds': {'type': 'integer'}
                                    }
                                }
                            },
                            'perm_banned': {
                                'type': 'array',
                                'items': {'type': 'string'}
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
@with_cookie_manager
def get_banned_accounts(cookie_manager):
    """获取被封禁的账号列表"""
    try:
        cursor = cookie_manager._get_cursor()
        
        # 获取临时封禁的账号
        cursor.execute("""
            SELECT DISTINCT account_id, MAX(temp_ban_until) as temp_ban_until
            FROM cookies 
            WHERE temp_ban_until IS NOT NULL AND temp_ban_until > NOW()
            AND is_permanently_banned = 0
            GROUP BY account_id
        """)
        temp_banned_accounts = cursor.fetchall()
        
        # 获取永久封禁的账号
        cursor.execute("""
            SELECT DISTINCT account_id
            FROM cookies 
            WHERE is_permanently_banned = 1
            GROUP BY account_id
        """)
        perm_banned_accounts = cursor.fetchall()
        
        # 处理临时封禁账号，计算剩余时间
        now = datetime.now()
        temp_banned_result = []
        for account in temp_banned_accounts:
            ban_until = account['temp_ban_until']
            remaining_seconds = int((ban_until - now).total_seconds())
            if remaining_seconds > 0:
                temp_banned_result.append({
                    'account_id': account['account_id'],
                    'temp_ban_until': ban_until.strftime('%Y-%m-%d %H:%M:%S'),
                    'remaining_seconds': remaining_seconds
                })
        
        # 处理永久封禁账号
        perm_banned_result = [account['account_id'] for account in perm_banned_accounts]
        
        result = {
            "temp_banned": temp_banned_result,
            "perm_banned": perm_banned_result
        }
        
        return jsonify(ResponseFormatter.success(result))
    except Exception as e:
        log.error(f"获取被封禁账号列表失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取被封禁账号列表失败: {str(e)}"))

@admin_cookie_bp.route('/update-ab-sr', methods=['POST'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '更新所有账号的ab_sr cookie',
    'description': '为所有账号获取最新的ab_sr cookie值，如果账号没有则添加',
    'responses': {
        '200': {
            'description': '更新成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '成功更新ab_sr cookie'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'updated_count': {'type': 'integer', 'description': '更新成功的账号数'},
                            'failed_count': {'type': 'integer', 'description': '更新失败的账号数'},
                            'added_count': {'type': 'integer', 'description': '新增ab_sr字段的账号数'}
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
@with_cookie_manager
def update_ab_sr(cookie_manager):
    """更新所有账号的ab_sr cookie值"""
    try:
        result = cookie_manager.update_ab_sr_for_all_accounts()
        
        if 'error' in result:
            return jsonify({
                'code': 10102,
                'msg': f"更新ab_sr cookie失败: {result['error']}",
                'data': result
            })
        
        return jsonify({
            'code': 10000,
            'msg': f"成功更新ab_sr cookie: 更新{result['updated_count']}个，新增{result['added_count']}个，失败{result['failed_count']}个",
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'code': 10102,
            'msg': f"更新ab_sr cookie失败: {str(e)}",
            'data': None
        })

@admin_cookie_bp.route('/sync-to-redis', methods=['POST'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '同步Cookie到Redis',
    'description': '将数据库中的Cookie数据同步到Redis缓存中',
    'responses': {
        '200': {
            'description': '同步成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': 'Cookie数据成功同步到Redis'},
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
@with_cookie_manager
def sync_to_redis(cookie_manager):
    """将数据库中的Cookie数据同步到Redis"""
    try:
        success = cookie_manager.sync_to_redis()
        
        if success:
            return jsonify(ResponseFormatter.success(None, "Cookie数据成功同步到Redis"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, "同步到Redis失败"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"同步到Redis失败: {str(e)}"))

@admin_cookie_bp.route('/usage', methods=['GET'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '获取Cookie使用量统计',
    'description': '获取指定时间范围内的Cookie使用量统计',
    'parameters': [
        {
            'name': 'account_id',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': '账号ID，用于过滤指定账号的使用量'
        },
        {
            'name': 'start_date',
            'in': 'query',
            'type': 'string',
            'format': 'date',
            'required': False,
            'description': '开始日期，格式为YYYY-MM-DD'
        },
        {
            'name': 'end_date',
            'in': 'query',
            'type': 'string',
            'format': 'date',
            'required': False,
            'description': '结束日期，格式为YYYY-MM-DD'
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
                                'usage_date': {'type': 'string', 'format': 'date'},
                                'usage_count': {'type': 'integer'}
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
def get_cookie_usage():
    """获取Cookie使用量统计"""
    try:
        # 获取查询参数
        account_id = request.args.get('account_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 导入cookie_rotator
        from cookie_manager.cookie_rotator import cookie_rotator
        
        # 获取使用量统计
        usage_data = cookie_rotator.get_cookie_usage(account_id, start_date, end_date)
        
        # 处理日期格式
        for item in usage_data:
            if 'usage_date' in item and item['usage_date']:
                item['usage_date'] = item['usage_date'].strftime('%Y-%m-%d')
        
        return jsonify(ResponseFormatter.success(usage_data))
    except Exception as e:
        log.error(f"获取Cookie使用量统计失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取Cookie使用量统计失败: {str(e)}"))

@admin_cookie_bp.route('/usage/today', methods=['GET'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '获取今日Cookie使用量',
    'description': '从Redis获取今日的Cookie使用量统计',
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
                        'additionalProperties': {
                            'type': 'integer'
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
def get_today_cookie_usage():
    """获取今日Cookie使用量"""
    try:
        # 导入cookie_rotator
        from cookie_manager.cookie_rotator import cookie_rotator
        
        # 获取今日使用量
        usage_data = cookie_rotator.get_today_usage_from_redis()
        
        return jsonify(ResponseFormatter.success(usage_data))
    except Exception as e:
        log.error(f"获取今日Cookie使用量失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取今日Cookie使用量失败: {str(e)}"))

@admin_cookie_bp.route('/usage/sync', methods=['POST'])
@swag_from({
    'tags': ['Cookie管理'],
    'summary': '同步Redis和MySQL中的Cookie使用量数据',
    'description': '手动同步Redis和MySQL中的Cookie使用量数据，确保两者一致',
    'responses': {
        '200': {
            'description': '同步成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '同步成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'synced_accounts': {'type': 'integer', 'description': '同步的账号数量'}
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
def sync_cookie_usage():
    """同步Redis和MySQL中的Cookie使用量数据"""
    try:
        # 导入cookie_rotator
        from cookie_manager.cookie_rotator import cookie_rotator
        
        # 手动调用同步方法
        cookie_rotator._sync_usage_data()
        
        # 获取同步后的使用量数据
        usage_data = cookie_rotator.get_today_usage_from_redis()
        
        return jsonify(ResponseFormatter.success({
            'synced_accounts': len(usage_data)
        }, "Cookie使用量数据同步成功"))
    except Exception as e:
        log.error(f"同步Cookie使用量数据失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"同步Cookie使用量数据失败: {str(e)}"))

# 注册蓝图的函数
def register_admin_cookie_blueprint(app):
    """注册Cookie管理API蓝图"""
    app.register_blueprint(admin_cookie_bp)
