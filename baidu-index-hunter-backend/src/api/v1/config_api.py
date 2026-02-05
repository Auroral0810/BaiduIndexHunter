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
from src.api.schemas.config import (
    ListConfigsRequest, 
    SetConfigRequest, 
    BatchSetConfigRequest,
    ConfigItemResponse,
    ConfigListResponse
)
from src.api.utils.validators import validate_json, validate_args
from src.api.utils.swagger import create_swagger_spec

# 创建蓝图
config_bp = Blueprint('config', __name__, url_prefix='/api/config')


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
        else:
            configs = config_manager.get_all()
        
        # 按键名排序
        sorted_configs = {k: configs[k] for k in sorted(configs.keys())}
        
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
        configs = validated_data.configs
        
        success_count = 0
        failed_keys = []
        
        for key, value in configs.items():
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
            ))
    except Exception as e:
        log.error(f"批量设置配置项失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"批量设置配置项失败: {str(e)}"))


@config_bp.route('/refresh', methods=['POST'])
@swag_from(REFRESH_CONFIG_SPEC)
def refresh_config():
    """刷新配置缓存"""
    try:
        config_manager.refresh()
        return jsonify(ResponseFormatter.success(None, "配置缓存刷新成功"))
    except Exception as e:
        log.error(f"刷新配置缓存失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"刷新配置缓存失败: {str(e)}"))


def register_config_blueprint(app):
    """注册配置API蓝图"""
    app.register_blueprint(config_bp)