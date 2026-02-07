"""
API 鉴权模块
使用 Bearer Token（API_SECRET_KEY）验证敏感接口
"""
from functools import wraps

from flask import request, jsonify
from src.core.config import API_CONFIG
from src.core.constants.respond import ResponseCode, ResponseFormatter


def _check_api_key():
    """
    检查请求是否携带有效的 Bearer Token。
    若 API_SECRET_KEY 为空（开发模式），则跳过鉴权。
    返回 None 表示通过，返回 (response, status_code) 表示拒绝。
    """
    secret = API_CONFIG.get('secret_key') or ''
    if not secret:
        return None
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        return jsonify(ResponseFormatter.error(
            ResponseCode.UNAUTHORIZED, "缺少 Authorization 头或格式错误，需要 Bearer Token"
        )), 401
    token = auth[7:].strip()
    if token != secret:
        return jsonify(ResponseFormatter.error(
            ResponseCode.UNAUTHORIZED, "Token 无效"
        )), 401
    return None


def require_api_key(f):
    """
    鉴权装饰器：要求请求头携带 Authorization: Bearer {API_SECRET_KEY}
    若 API_SECRET_KEY 为空（开发模式），则跳过鉴权
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        result = _check_api_key()
        if result is not None:
            return result
        return f(*args, **kwargs)
    return decorated


def auth_before_request():
    """
    供 blueprint.before_request 使用的鉴权函数。
    返回 None 表示通过，返回 Response 表示拒绝并终止请求。
    """
    result = _check_api_key()
    if result is not None:
        resp, status_code = result
        resp.status_code = status_code
        return resp
    return None
