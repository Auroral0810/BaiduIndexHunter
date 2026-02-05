"""
Cookie管理控制器 - 提供Cookie管理的API接口
"""
from flask import Blueprint, request, jsonify, g
import json
from datetime import datetime, timedelta
from flasgger import swag_from
import pymysql
import traceback
import functools

from src.services.cookie_service import CookieManager
from src.core.constants.respond import ResponseCode, ResponseFormatter
from src.core.config import MYSQL_CONFIG
from src.core.logger import log
from src.api.schemas.cookie import (
    AddCookieRequest,
    BanAccountRequest,
    UpdateCookieRequest,
    UpdateAccountIdRequest,
    ListCookiesRequest,
    CookieListResponse,
    CookiePoolStatusResponse,
    SyncResultResponse,
    TestResultResponse,
    TodayCookieUsageResponse
)
from src.api.utils.validators import validate_json, validate_args
from src.api.utils.swagger import create_swagger_spec

# 创建蓝图
admin_cookie_bp = Blueprint('admin_cookie', __name__, url_prefix='/api/admin/cookie')


# ============== Swagger 规范定义 ==============

LIST_COOKIES_SPEC = create_swagger_spec(
    request_schema=ListCookiesRequest,
    response_schema=CookieListResponse,
    summary="获取Cookie列表",
    description="获取所有Cookie或根据账号ID过滤",
    tags=["Cookie管理"],
    request_in="query"
)

GET_ASSEMBLED_COOKIES_SPEC = create_swagger_spec(
    summary="获取组装后的完整Cookie字典",
    tags=["Cookie管理"]
)

LIST_ACCOUNTS_SPEC = create_swagger_spec(
    summary="获取所有可用的账号ID",
    tags=["Cookie管理"]
)

ADD_COOKIE_SPEC = create_swagger_spec(
    request_schema=AddCookieRequest,
    summary="添加Cookie",
    tags=["Cookie管理"],
    request_in="body"
)

DELETE_COOKIE_SPEC = create_swagger_spec(
    summary="删除指定账号的所有Cookie",
    tags=["Cookie管理"],
    parameters=[{
        'name': 'account_id',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': '账号ID'
    }]
)

UPDATE_COOKIE_SPEC = create_swagger_spec(
    request_schema=UpdateCookieRequest,
    summary="更新指定Cookie",
    tags=["Cookie管理"],
    parameters=[{
        'name': 'account_id',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': '账号ID'
    }],
    request_in="body"
)

BAN_ACCOUNT_PERM_SPEC = create_swagger_spec(
    summary="永久封禁账号",
    tags=["Cookie管理"],
    parameters=[{
        'name': 'account_id',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': '账号ID'
    }]
)

BAN_ACCOUNT_TEMP_SPEC = create_swagger_spec(
    request_schema=BanAccountRequest,
    summary="临时封禁账号",
    tags=["Cookie管理"],
    parameters=[{
        'name': 'account_id',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': '账号ID'
    }],
    request_in="body"
)

UNBAN_ACCOUNT_SPEC = create_swagger_spec(
    summary="解封账号（只解封临时封禁的）",
    tags=["Cookie管理"],
    parameters=[{
        'name': 'account_id',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': '账号ID'
    }]
)

FORCE_UNBAN_ACCOUNT_SPEC = create_swagger_spec(
    summary="强制解封账号（包括永久封禁的）",
    tags=["Cookie管理"],
    parameters=[{
        'name': 'account_id',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': '账号ID'
    }]
)

UPDATE_COOKIE_STATUS_SPEC = create_swagger_spec(
    summary="检查并更新Cookie状态",
    description="将临时封禁过期的Cookie恢复可用",
    tags=["Cookie管理"]
)

CLEANUP_EXPIRED_COOKIES_SPEC = create_swagger_spec(
    summary="清理已过期的Cookie",
    tags=["Cookie管理"]
)

UPDATE_ACCOUNT_ID_SPEC = create_swagger_spec(
    request_schema=UpdateAccountIdRequest,
    summary="更新账号ID",
    tags=["Cookie管理"],
    parameters=[{
        'name': 'old_account_id',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': '旧账号ID'
    }],
    request_in="body"
)

TEST_COOKIE_AVAILABILITY_SPEC = create_swagger_spec(
    response_schema=TestResultResponse,
    summary="测试所有可用Cookie的可用性",
    tags=["Cookie管理"]
)

TEST_ACCOUNT_COOKIE_SPEC = create_swagger_spec(
    summary="测试单个账号的Cookie可用性",
    tags=["Cookie管理"],
    parameters=[{
        'name': 'account_id',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': '账号ID'
    }]
)

GET_AVAILABLE_ACCOUNT_IDS_SPEC = create_swagger_spec(
    summary="获取所有可用的账号ID列表",
    tags=["Cookie管理"]
)

GET_ACCOUNT_COOKIE_SPEC = create_swagger_spec(
    summary="获取指定账号ID的Cookie详细信息",
    tags=["Cookie管理"],
    parameters=[{
        'name': 'account_id',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': '账号ID'
    }]
)

GET_POOL_STATUS_SPEC = create_swagger_spec(
    response_schema=CookiePoolStatusResponse,
    summary="获取Cookie池状态",
    tags=["Cookie管理"]
)

GET_BANNED_ACCOUNTS_SPEC = create_swagger_spec(
    summary="获取被封禁的账号列表",
    tags=["Cookie管理"]
)

UPDATE_AB_SR_SPEC = create_swagger_spec(
    summary="更新所有账号的ab_sr cookie值",
    tags=["Cookie管理"]
)

SYNC_TO_REDIS_SPEC = create_swagger_spec(
    response_schema=SyncResultResponse,
    summary="将数据库中的Cookie数据同步到Redis",
    tags=["Cookie管理"]
)

GET_COOKIE_USAGE_SPEC = create_swagger_spec(
    summary="获取Cookie使用量统计",
    tags=["Cookie管理"]
)

GET_TODAY_COOKIE_USAGE_SPEC = create_swagger_spec(
    response_schema=TodayCookieUsageResponse,
    summary="获取今日Cookie使用量",
    tags=["Cookie管理"]
)

SYNC_COOKIE_USAGE_SPEC = create_swagger_spec(
    response_schema=SyncResultResponse,
    summary="同步Redis和MySQL中的Cookie使用量数据",
    tags=["Cookie管理"]
)


# ============== 辅助函数 ==============

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


# ============== API 端点 ==============



@admin_cookie_bp.route('/list', methods=['GET'])
@swag_from(LIST_COOKIES_SPEC)
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
@swag_from(GET_ASSEMBLED_COOKIES_SPEC)
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
@swag_from(LIST_ACCOUNTS_SPEC)
@with_cookie_manager
def list_accounts(cookie_manager):
    """获取所有可用的账号ID"""
    try:
        account_ids = cookie_manager.get_available_account_ids()
        return jsonify(ResponseFormatter.success(account_ids))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取账号列表失败: {str(e)}"))

@admin_cookie_bp.route('/add', methods=['POST'])
@swag_from(ADD_COOKIE_SPEC)
@with_cookie_manager
@validate_json(AddCookieRequest, inject_as_arg=False)
def add_cookie(cookie_manager):
    """添加Cookie"""
    try:
        # 从 flask.g 获取校验后的数据
        validated_data: AddCookieRequest = g.validated_data
        
        account_id = validated_data.account_id
        cookie_data = validated_data.cookie_data
        expire_days = validated_data.expire_days
        
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
@swag_from(DELETE_COOKIE_SPEC)
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
@swag_from(UPDATE_COOKIE_SPEC)
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
@swag_from(BAN_ACCOUNT_PERM_SPEC)
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
@swag_from(BAN_ACCOUNT_TEMP_SPEC)
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
@swag_from(UNBAN_ACCOUNT_SPEC)
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
@swag_from(FORCE_UNBAN_ACCOUNT_SPEC)
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
@swag_from(UPDATE_COOKIE_STATUS_SPEC)
@with_cookie_manager
def update_cookie_status(cookie_manager):
    """检查并更新Cookie状态，将临时封禁过期的Cookie恢复可用"""
    try:
        updated_count = cookie_manager.check_and_update_cookie_status()
        
        return jsonify(ResponseFormatter.success({"updated_count": updated_count}, f"成功更新{updated_count}条Cookie状态"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"更新Cookie状态失败: {str(e)}"))

@admin_cookie_bp.route('/cleanup-expired', methods=['POST'])
@swag_from(CLEANUP_EXPIRED_COOKIES_SPEC)
@with_cookie_manager
def cleanup_expired_cookies(cookie_manager):
    """清理已过期的Cookie"""
    try:
        deleted_count = cookie_manager.cleanup_expired_cookies()
        
        return jsonify(ResponseFormatter.success({"deleted_count": deleted_count}, f"成功清理{deleted_count}条过期Cookie"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"清理过期Cookie失败: {str(e)}"))

@admin_cookie_bp.route('/update-account/<old_account_id>', methods=['PUT'])
@swag_from(UPDATE_ACCOUNT_ID_SPEC)
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
@swag_from(TEST_ACCOUNT_COOKIE_SPEC)
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
@swag_from(GET_AVAILABLE_ACCOUNT_IDS_SPEC)
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
@swag_from(GET_ACCOUNT_COOKIE_SPEC)
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
@swag_from(GET_POOL_STATUS_SPEC)
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
@swag_from(GET_BANNED_ACCOUNTS_SPEC)
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
        from src.services.cookie_rotator import cookie_rotator
        
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
        from src.services.cookie_rotator import cookie_rotator
        
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
        from src.services.cookie_rotator import cookie_rotator
        
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
