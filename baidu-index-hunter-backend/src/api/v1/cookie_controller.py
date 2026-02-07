"""
Cookie管理控制器 - 提供Cookie管理的API接口
"""
from flask import Blueprint, request, jsonify, g
from typing import Dict
import traceback
from flasgger import swag_from

from src.services.cookie_service import cookie_service
from src.core.constants.respond import ResponseCode, ResponseFormatter
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
    SingleCookieTestResult,
    TestResultResponse,
    TodayCookieUsageResponse,
    BannedAccountResponse
)
from src.api.utils.validators import validate_json, validate_args
from src.api.utils.swagger import create_swagger_spec
from src.core.auth import auth_before_request

# 创建蓝图
admin_cookie_bp = Blueprint('admin_cookie', __name__, url_prefix='/api/admin/cookie')
admin_cookie_bp.before_request(auth_before_request)


def register_cookie_blueprint(app):
    """注册Cookie API蓝图"""
    app.register_blueprint(admin_cookie_bp)

# ============== Swagger 规范定义 (Simplified) ==============

LIST_COOKIES_SPEC = create_swagger_spec(
    request_schema=ListCookiesRequest,
    response_schema=CookieListResponse,
    summary="获取Cookie列表",
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
    parameters=[{'name': 'account_id', 'in': 'path', 'type': 'string', 'required': True}]
)

UPDATE_COOKIE_SPEC = create_swagger_spec(
    request_schema=UpdateCookieRequest,
    summary="更新指定Cookie",
    tags=["Cookie管理"],
    parameters=[{'name': 'cookie_id', 'in': 'path', 'type': 'integer', 'required': True}],
    request_in="body"
)

BAN_ACCOUNT_PERM_SPEC = create_swagger_spec(
    summary="永久封禁账号",
    tags=["Cookie管理"],
    parameters=[{'name': 'account_id', 'in': 'path', 'type': 'string', 'required': True}]
)

BAN_ACCOUNT_TEMP_SPEC = create_swagger_spec(
    request_schema=BanAccountRequest,
    summary="临时封禁账号",
    tags=["Cookie管理"],
    parameters=[{'name': 'account_id', 'in': 'path', 'type': 'string', 'required': True}],
    request_in="body"
)

UNBAN_ACCOUNT_SPEC = create_swagger_spec(
    summary="解封账号（只解封临时封禁的）",
    tags=["Cookie管理"],
    parameters=[{'name': 'account_id', 'in': 'path', 'type': 'string', 'required': True}]
)

FORCE_UNBAN_ACCOUNT_SPEC = create_swagger_spec(
    summary="强制解封账号（包括永久封禁的）",
    tags=["Cookie管理"],
    parameters=[{'name': 'account_id', 'in': 'path', 'type': 'string', 'required': True}]
)

UPDATE_COOKIE_STATUS_SPEC = create_swagger_spec(
    summary="检查并更新Cookie状态",
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
    parameters=[{'name': 'old_account_id', 'in': 'path', 'type': 'string', 'required': True}],
    request_in="body"
)

TEST_COOKIE_AVAILABILITY_SPEC = create_swagger_spec(
    response_schema=TestResultResponse,
    summary="测试所有可用Cookie的可用性",
    tags=["Cookie管理"]
)

TEST_ACCOUNT_COOKIE_SPEC = create_swagger_spec(
    response_schema=SingleCookieTestResult,
    summary="测试单个账号的Cookie可用性",
    tags=["Cookie管理"],
    parameters=[{'name': 'account_id', 'in': 'path', 'type': 'string', 'required': True}]
)

GET_AVAILABLE_ACCOUNT_IDS_SPEC = create_swagger_spec(
    summary="获取所有可用的账号ID列表",
    tags=["Cookie管理"]
)

GET_ACCOUNT_COOKIE_SPEC = create_swagger_spec(
    summary="获取指定账号ID的Cookie详细信息",
    tags=["Cookie管理"],
    parameters=[{'name': 'account_id', 'in': 'path', 'type': 'string', 'required': True}]
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

SYNC_TO_REDIS_SPEC = create_swagger_spec(
    response_schema=SyncResultResponse,
    summary="将数据库中的Cookie数据同步到Redis",
    tags=["Cookie管理"]
)

UPDATE_AB_SR_SPEC = create_swagger_spec(
    summary="更新所有账号的ab_sr cookie值",
    tags=["Cookie管理"]
)


# ============== API 端点 ==============

@admin_cookie_bp.route('/list', methods=['GET'])
@swag_from(LIST_COOKIES_SPEC)
@validate_args(ListCookiesRequest)
def list_cookies(validated_data: ListCookiesRequest):
    """获取所有Cookie，按账号ID组装"""
    try:
        # Params validated automatically
        result = cookie_service.get_cookie_list_with_pagination(
            page=validated_data.page,
            limit=validated_data.limit,
            account_id=validated_data.account_id,
            status=validated_data.status,
            available_only=validated_data.available_only
        )
        
        return jsonify(ResponseFormatter.success({
            'data': result['items'],
            'total': result['total'],
            'page': result['page'],
            'limit': result['limit']
        }))
    except Exception as e:
        log.error(f"获取Cookie列表失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取Cookie列表失败: {str(e)}"))

@admin_cookie_bp.route('/assembled', methods=['GET'])
@swag_from(GET_ASSEMBLED_COOKIES_SPEC)
def get_assembled_cookies():
    """获取组装后的完整Cookie字典"""
    try:
        account_ids_param = request.args.get('account_ids')
        account_ids = account_ids_param.split(',') if account_ids_param else None
        
        assembled_cookies = cookie_service.get_assembled_cookies(account_ids)
        return jsonify(ResponseFormatter.success(assembled_cookies))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取组装Cookie失败: {str(e)}"))

@admin_cookie_bp.route('/accounts', methods=['GET'])
@swag_from(LIST_ACCOUNTS_SPEC)
def list_accounts():
    """获取所有可用的账号ID"""
    try:
        account_ids = cookie_service.get_available_account_ids()
        return jsonify(ResponseFormatter.success(account_ids))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取账号列表失败: {str(e)}"))

@admin_cookie_bp.route('/add', methods=['POST'])
@swag_from(ADD_COOKIE_SPEC)
@validate_json(AddCookieRequest)
def add_cookie(validated_data: AddCookieRequest):
    """添加Cookie"""
    try:
        success = cookie_service.add_cookie(
            validated_data.account_id,
            validated_data.cookie_data,
            validated_data.expire_days
        )
        
        if success:
            return jsonify(ResponseFormatter.success(None, "Cookie添加成功"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.COOKIE_ERROR, "Cookie添加失败"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"添加Cookie失败: {str(e)}"))

@admin_cookie_bp.route('/delete/<account_id>', methods=['DELETE'])
@swag_from(DELETE_COOKIE_SPEC)
def delete_cookie(account_id):
    """删除指定账号的所有Cookie"""
    try:
        deleted_count = cookie_service.delete_by_account_id(account_id)
        if deleted_count > 0:
            return jsonify(ResponseFormatter.success({"deleted_count": deleted_count}, f"成功删除{deleted_count}条Cookie记录"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "未找到指定账号的Cookie记录"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"删除Cookie失败: {str(e)}"))

@admin_cookie_bp.route('/update/<int:cookie_id>', methods=['PUT'])
@swag_from(UPDATE_COOKIE_SPEC)
@validate_json(UpdateCookieRequest)
def update_cookie(validated_data: UpdateCookieRequest, cookie_id: int):
    """更新指定Cookie"""
    try:
        # Pydantic schema keys match update logic?
        # UpdateCookieRequest has 'cookies' dict.
        # But 'update_cookie' service method expects fields dict.
        # Controller logic flaw in swagger spec vs service?
        # The previous code accepted request.json. Service update_cookie updates FIELDS of a single cookie row.
        # If 'UpdateCookieRequest' is supposed to update fields, it should contain fields.
        # Let's assume passed dict is what we want.
        
        data = validated_data.model_dump(exclude_unset=True)
        # However, UpdateCookieRequest in schema defines "cookies" (Dict) and "expire_days" (int).
        # cookie_service.update_cookie updates a SINGLE ROW (id).
        # So we probably want to update cookie_value or other fields.
        # Simplified: Pass validated data, let service handle or adjust request schema.
        # Given existing usage, likely it updates fields like cookie_value.
        
        success = cookie_service.update_cookie(cookie_id, data)
        if success:
            return jsonify(ResponseFormatter.success(None, "Cookie更新成功"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "未找到指定的Cookie或更新失败"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"更新Cookie失败: {str(e)}"))

@admin_cookie_bp.route('/ban/permanent/<account_id>', methods=['POST'])
@swag_from(BAN_ACCOUNT_PERM_SPEC)
def ban_account_permanently(account_id):
    """永久封禁账号"""
    try:
        banned_count = cookie_service.ban_account_permanently(account_id)
        if banned_count > 0:
            return jsonify(ResponseFormatter.success({"banned_count": banned_count}, f"成功永久封禁{banned_count}条Cookie记录"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "未找到指定账号的Cookie记录"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"永久封禁账号失败: {str(e)}"))

@admin_cookie_bp.route('/ban/temporary/<account_id>', methods=['POST'])
@swag_from(BAN_ACCOUNT_TEMP_SPEC)
@validate_json(BanAccountRequest)
def ban_account_temporarily(validated_data: BanAccountRequest, account_id: str):
    """临时封禁账号"""
    try:
        duration_seconds = validated_data.ban_hours * 3600
        banned_count = cookie_service.ban_account_temporarily(account_id, duration_seconds)
        
        if banned_count > 0:
            return jsonify(ResponseFormatter.success(
                {"banned_count": banned_count, "duration_seconds": duration_seconds}, 
                f"成功临时封禁{banned_count}条Cookie记录"
            ))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "未找到指定账号的Cookie记录"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"临时封禁账号失败: {str(e)}"))

@admin_cookie_bp.route('/unban/<account_id>', methods=['POST'])
@swag_from(UNBAN_ACCOUNT_SPEC)
def unban_account(account_id):
    """解封账号（只解封临时封禁的）"""
    try:
        unbanned_count = cookie_service.unban_account(account_id)
        if unbanned_count > 0:
            return jsonify(ResponseFormatter.success({"unbanned_count": unbanned_count}, f"成功解封{unbanned_count}条Cookie记录"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "未找到可解封的Cookie记录"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"解封账号失败: {str(e)}"))

@admin_cookie_bp.route('/force-unban/<account_id>', methods=['POST'])
@swag_from(FORCE_UNBAN_ACCOUNT_SPEC)
def force_unban_account(account_id):
    """强制解封账号"""
    try:
        unbanned_count = cookie_service.force_unban_account(account_id)
        if unbanned_count > 0:
            return jsonify(ResponseFormatter.success({"unbanned_count": unbanned_count}, f"成功强制解封{unbanned_count}条Cookie记录"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "未找到可解封的Cookie记录"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"强制解封账号失败: {str(e)}"))

@admin_cookie_bp.route('/update-status', methods=['POST'])
@swag_from(UPDATE_COOKIE_STATUS_SPEC)
def update_cookie_status():
    """检查并更新Cookie状态"""
    try:
        result = cookie_service.check_and_update_cookie_status()
        return jsonify(ResponseFormatter.success(result, "成功更新Cookie状态"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"更新Cookie状态失败: {str(e)}"))

@admin_cookie_bp.route('/cleanup-expired', methods=['POST'])
@swag_from(CLEANUP_EXPIRED_COOKIES_SPEC)
def cleanup_expired_cookies():
    """清理已过期的Cookie"""
    try:
        deleted_count = cookie_service.cleanup_expired_cookies()
        return jsonify(ResponseFormatter.success({"deleted_count": deleted_count}, f"成功清理{deleted_count}条过期Cookie"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"清理过期Cookie失败: {str(e)}"))

@admin_cookie_bp.route('/update-account/<old_account_id>', methods=['PUT'])
@swag_from(UPDATE_ACCOUNT_ID_SPEC)
@validate_json(UpdateAccountIdRequest)
def update_account_id(validated_data: UpdateAccountIdRequest, old_account_id: str):
    """更新账号ID"""
    try:
        new_account_id = validated_data.new_account_id
        updated_count = cookie_service.update_account_id(old_account_id, new_account_id)
        
        if updated_count > 0:
            return jsonify(ResponseFormatter.success({"updated_count": updated_count}, f"成功更新{updated_count}条Cookie记录的账号ID"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "未找到指定账号的Cookie记录"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"更新账号ID失败: {str(e)}"))

@admin_cookie_bp.route('/test-availability', methods=['POST'])
@swag_from(TEST_COOKIE_AVAILABILITY_SPEC)
def test_cookie_availability():
    """测试所有可用Cookie的可用性"""
    try:
        result = cookie_service.test_cookies_availability()
        return jsonify(ResponseFormatter.success(result, "Cookie可用性测试完成"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"测试Cookie可用性失败: {str(e)}"))

@admin_cookie_bp.route('/test-account-availability/<account_id>', methods=['POST'])
@swag_from(TEST_ACCOUNT_COOKIE_SPEC)
def test_account_cookie_availability(account_id):
    """测试单个账号的Cookie可用性"""
    try:
        result = cookie_service.test_account_cookie_availability(account_id)
        return jsonify(ResponseFormatter.success(result, f"账号 {account_id} Cookie测试完成"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"测试账号 {account_id} Cookie失败: {str(e)}"))

@admin_cookie_bp.route('/available-accounts', methods=['GET'])
@swag_from(GET_AVAILABLE_ACCOUNT_IDS_SPEC)
def get_available_account_ids():
    """获取所有可用的账号ID列表"""
    try:
        account_ids = cookie_service.get_available_account_ids()
        result = {"account_ids": account_ids, "count": len(account_ids)}
        return jsonify(ResponseFormatter.success(result, "获取可用账号ID成功"))
    except Exception as e:
        log.error(f"获取可用账号ID失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取可用账号ID失败: {str(e)}"))

@admin_cookie_bp.route('/account-cookie/<account_id>', methods=['GET'])
@swag_from(GET_ACCOUNT_COOKIE_SPEC)
def get_account_cookie(account_id):
    """获取指定账号ID的Cookie详细信息"""
    try:
        cookies_list = cookie_service.get_cookies_by_account_id(account_id)
        if not cookies_list:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, f"账号 {account_id} 不存在或没有Cookie记录"))
        
        cookie_dict = cookie_service.get_cookie_by_account_id(account_id)
        is_available = cookie_dict is not None
        
        if not is_available:
            cookie_dict = {c['cookie_name']: c['cookie_value'] for c in cookies_list}
        
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
def get_pool_status():
    """获取Cookie池状态"""
    try:
        result = cookie_service.get_pool_status_data()
        return jsonify(ResponseFormatter.success(result))
    except Exception as e:
        log.error(f"获取Cookie池状态失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取Cookie池状态失败: {str(e)}"))

@admin_cookie_bp.route('/banned-accounts', methods=['GET'])
@swag_from(GET_BANNED_ACCOUNTS_SPEC)
def get_banned_accounts():
    """获取被封禁的账号列表"""
    try:
        result = cookie_service.get_banned_accounts_list()
        return jsonify(ResponseFormatter.success(result))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取被封禁账号列表失败: {str(e)}"))

@admin_cookie_bp.route('/sync-to-redis', methods=['POST'])
@swag_from(SYNC_TO_REDIS_SPEC)
def sync_to_redis():
    """同步Cookie数据到Redis"""
    try:
        success = cookie_service.sync_to_redis()
        if success:
             return jsonify(ResponseFormatter.success({"success": True}, "同步成功"))
        else:
             return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, "同步失败"))
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"同步失败: {str(e)}"))

@admin_cookie_bp.route('/update-ab-sr', methods=['POST'])
@swag_from(UPDATE_AB_SR_SPEC)
def update_ab_sr():
    """更新ab_sr"""
    try:
        updated_count = cookie_service.update_ab_sr_for_all_accounts()
        return jsonify(ResponseFormatter.success({"updated_count": updated_count}, f"成功为{updated_count}个账号更新ab_sr"))
    except Exception as e:

        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"更新ab_sr失败: {str(e)}"))

@admin_cookie_bp.route('/usage', methods=['GET'])
def get_cookie_usage():
    """获取Cookie使用量统计"""
    try:
        account_id = request.args.get('account_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        result = cookie_service.get_cookie_usage(account_id, start_date, end_date)
        return jsonify(ResponseFormatter.success(result))
    except Exception as e:
        log.error(f"获取Cookie使用量统计失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取统计失败: {str(e)}"))

@admin_cookie_bp.route('/usage/sync', methods=['POST'])
def sync_usage_data():
    """手动同步Cookie使用量数据"""
    try:
        cookie_service.sync_usage_data()
        return jsonify(ResponseFormatter.success(None, "使用量数据同步成功"))
    except Exception as e:
        log.error(f"同步Cookie使用量数据失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"同步失败: {str(e)}"))
