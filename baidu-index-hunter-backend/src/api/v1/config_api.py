"""
配置API模块
提供配置管理的API接口
"""
import os
import json
from flask import Blueprint, request, jsonify
from flasgger import swag_from

from src.services.config_service import config_manager
from src.core.logger import log
from src.core.constants.respond import ResponseCode, ResponseFormatter
from src.api.schemas.config import (
    ListConfigsRequest, 
    SetConfigRequest, 
    BatchSetConfigRequest,
    ConfigItemResponse,
    ConfigListResponse
)
from src.api.utils.validators import validate_json, validate_args
from src.api.utils.swagger import create_swagger_spec
from src.core.auth import auth_before_request

# 创建蓝图
config_bp = Blueprint('config', __name__, url_prefix='/api/config')
config_bp.before_request(auth_before_request)


# ============== Swagger 规范定义 ==============

LIST_CONFIGS_SPEC = create_swagger_spec(
    request_schema=ListConfigsRequest,
    response_schema=ConfigListResponse,
    summary="获取配置列表",
    description="获取所有配置项或根据前缀过滤",
    tags=["系统配置"],
    request_in="query"
)

GET_CONFIG_SPEC = create_swagger_spec(
    response_schema=ConfigItemResponse,
    summary="获取单个配置项",
    description="根据配置键获取单个配置项的值",
    tags=["系统配置"],
    parameters=[{
        'name': 'key',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': '配置键'
    }]
)

SET_CONFIG_SPEC = create_swagger_spec(
    request_schema=SetConfigRequest,
    summary="设置配置项",
    description="设置单个配置项的值",
    tags=["系统配置"],
    request_in="body"
)

DELETE_CONFIG_SPEC = create_swagger_spec(
    summary="删除配置项",
    description="删除指定的配置项",
    tags=["系统配置"],
    parameters=[{
        'name': 'key',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': '要删除的配置键'
    }]
)

BATCH_SET_CONFIG_SPEC = create_swagger_spec(
    request_schema=BatchSetConfigRequest,
    summary="批量设置配置项",
    description="批量设置多个配置项的值",
    tags=["系统配置"],
    request_in="body"
)

REFRESH_CONFIG_SPEC = create_swagger_spec(
    summary="刷新配置缓存",
    description="从数据库重新加载所有配置项，刷新缓存",
    tags=["系统配置"]
)


# ============== API 端点 ==============

@config_bp.route('/list', methods=['GET'])
@swag_from(LIST_CONFIGS_SPEC)
@validate_args(ListConfigsRequest)
def list_configs(validated_data: ListConfigsRequest):
    """获取所有配置项"""
    try:
        prefix = validated_data.prefix or ''
        
        if prefix:
            configs = config_manager.get_by_prefix(prefix)
            # Sort locally for prefix search
            sorted_configs = {k: configs[k] for k in sorted(configs.keys())}
        else:
            sorted_configs = config_manager.get_all_sorted()
        
        return jsonify(ResponseFormatter.success(sorted_configs))
    except Exception as e:
        log.error(f"获取配置列表失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取配置列表失败: {str(e)}"))


@config_bp.route('/get/<string:key>', methods=['GET'])
@swag_from(GET_CONFIG_SPEC)
def get_config(key):
    """获取单个配置项"""
    try:
        value = config_manager.get(key)
        
        if value is None:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, f"配置项 '{key}' 不存在"))
        
        return jsonify(ResponseFormatter.success({
            'key': key,
            'value': value
        }))
    except Exception as e:
        log.error(f"获取配置项失败: {key} - {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取配置项失败: {str(e)}"))


@config_bp.route('/set', methods=['POST'])
@swag_from(SET_CONFIG_SPEC)
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
            return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"配置项 '{key}' 设置失败"))
    except Exception as e:
        log.error(f"设置配置项失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"设置配置项失败: {str(e)}"))


@config_bp.route('/delete/<string:key>', methods=['DELETE'])
@swag_from(DELETE_CONFIG_SPEC)
def delete_config(key):
    """删除配置项"""
    try:
        success = config_manager.delete(key)
        
        if success:
            return jsonify(ResponseFormatter.success(None, f"配置项 '{key}' 删除成功"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"配置项 '{key}' 删除失败"))
    except Exception as e:
        log.error(f"删除配置项失败: {key} - {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"删除配置项失败: {str(e)}"))


@config_bp.route('/batch_set', methods=['POST'])
@swag_from(BATCH_SET_CONFIG_SPEC)
@validate_json(BatchSetConfigRequest)
def batch_set_config(validated_data: BatchSetConfigRequest):
    """批量设置配置项"""
    try:
        configs = validated_data.root
        
        success_count, failed_keys = config_manager.batch_set(configs)
        
        if not failed_keys:
            return jsonify(ResponseFormatter.success(None, f"所有配置项设置成功，共 {success_count} 项"))
        else:
            return jsonify(ResponseFormatter.error(
                ResponseCode.SERVER_ERROR, 
                f"部分配置项设置失败: {', '.join(failed_keys)}，成功 {success_count} 项"
            ))
    except Exception as e:
        log.error(f"批量设置配置项失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"批量设置配置项失败: {str(e)}"))


@config_bp.route('/refresh', methods=['POST'])
@swag_from(REFRESH_CONFIG_SPEC)
def refresh_config():
    """刷新配置缓存"""
    try:
        config_manager.refresh_cache()
        return jsonify(ResponseFormatter.success(None, "配置缓存刷新成功"))
    except Exception as e:
        log.error(f"刷新配置缓存失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"刷新配置缓存失败: {str(e)}"))


def _get_allowed_roots():
    """获取允许浏览/操作的根路径列表，防止路径遍历"""
    roots = []
    user_home = os.path.expanduser('~')
    if user_home:
        roots.append(os.path.realpath(user_home))
    default_dir = config_manager.get('output.default_dir') or ''
    if default_dir:
        expanded = os.path.abspath(os.path.expanduser(default_dir))
        if os.path.isdir(expanded):
            roots.append(os.path.realpath(expanded))
    if not roots:
        roots.append(os.path.realpath(user_home or '/'))
    return roots


def _is_path_allowed(abs_path: str) -> bool:
    """检查路径是否在允许的白名单根路径之下"""
    try:
        real = os.path.realpath(abs_path)
        roots = _get_allowed_roots()
        for root in roots:
            if real == root or real.startswith(root + os.sep):
                return True
        return False
    except (OSError, ValueError):
        return False


@config_bp.route('/browse_dir', methods=['GET'])
def browse_directory():
    """
    浏览目录结构（用于前端选择输出目录）。
    安全限制：仅允许浏览用户家目录及配置的默认输出目录及其子目录。
    Query params:
      - path: 要浏览的目录路径（为空则返回常用根路径）
    Returns:
      - current: 当前目录的绝对路径
      - parent: 父目录路径
      - dirs: 子目录列表
    """
    try:
        target_path = request.args.get('path', '').strip()
        
        if not target_path:
            # 返回当前默认输出目录，若不存在则回退到用户家目录
            default_dir = config_manager.get('output.default_dir') or ''
            if default_dir and os.path.isdir(os.path.abspath(os.path.expanduser(default_dir))):
                target_path = default_dir
            else:
                target_path = os.path.expanduser('~')
        
        target_path = os.path.abspath(os.path.expanduser(target_path))
        
        if not os.path.isdir(target_path):
            # 路径不存在时回退到用户家目录
            target_path = os.path.expanduser('~')
            target_path = os.path.abspath(target_path)
        
        if not _is_path_allowed(target_path):
            return jsonify(ResponseFormatter.error(
                ResponseCode.PARAM_ERROR, "无权访问该路径，仅允许浏览用户目录及输出目录"
            ))
        
        # 列出子目录（忽略隐藏目录和无权限目录）
        dirs = []
        try:
            for entry in sorted(os.listdir(target_path)):
                full = os.path.join(target_path, entry)
                if os.path.isdir(full) and not entry.startswith('.'):
                    full_real = os.path.realpath(full)
                    if _is_path_allowed(full_real):
                        dirs.append(entry)
        except PermissionError:
            pass
        
        parent = os.path.dirname(target_path)
        if parent != target_path and not _is_path_allowed(parent):
            parent = None
        
        return jsonify(ResponseFormatter.success({
            'current': target_path,
            'parent': parent if parent != target_path else None,
            'dirs': dirs
        }))
    except Exception as e:
        log.error(f"浏览目录失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"浏览目录失败: {str(e)}"))


@config_bp.route('/validate_path', methods=['POST'])
def validate_path():
    """
    验证路径是否可用（存在或可创建）。
    安全限制：仅允许在用户家目录及配置的默认输出目录之下操作。
    Body: { "path": "/some/path", "create": false }
    Returns: { "valid": true, "absolute_path": "/absolute/some/path", "exists": true }
    """
    try:
        data = request.get_json(silent=True) or {}
        path_str = (data.get('path') or '').strip()
        should_create = data.get('create', False)
        
        if not path_str:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "路径不能为空"))
        
        abs_path = os.path.abspath(os.path.expanduser(path_str))
        
        # 安全检查：路径必须在允许的根路径之下
        if not _is_path_allowed(abs_path):
            return jsonify(ResponseFormatter.error(
                ResponseCode.PARAM_ERROR, "无权操作该路径，仅允许在用户目录及输出目录下创建"
            ))
        
        exists = os.path.isdir(abs_path)
        
        # 如果要求实际创建目录
        if should_create and not exists:
            try:
                os.makedirs(abs_path, exist_ok=True)
                return jsonify(ResponseFormatter.success({
                    'valid': True,
                    'absolute_path': abs_path,
                    'exists': True,
                    'created': True
                }))
            except (OSError, PermissionError) as e:
                return jsonify(ResponseFormatter.error(
                    ResponseCode.SERVER_ERROR, f"无法创建目录: {str(e)}"
                ))
        
        # 仅验证模式：检查是否可创建
        can_create = False
        if not exists:
            try:
                os.makedirs(abs_path, exist_ok=True)
                can_create = True
                # 创建成功后如果原来不存在则删除（只验证，不实际创建）
                os.rmdir(abs_path)
            except (OSError, PermissionError):
                can_create = False
        
        return jsonify(ResponseFormatter.success({
            'valid': exists or can_create,
            'absolute_path': abs_path,
            'exists': exists
        }))
    except Exception as e:
        log.error(f"验证路径失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"验证路径失败: {str(e)}"))


def register_config_blueprint(app):
    """注册配置API蓝图"""
    app.register_blueprint(config_bp)