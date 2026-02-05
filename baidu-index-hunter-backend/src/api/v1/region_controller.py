#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
区域数据API控制器
提供百度指数区域代码相关的API接口
"""

from flask import Blueprint, request, jsonify
from flasgger import swag_from
from src.services.region_service import get_region_manager
from src.core.constants.respond import ResponseCode, ResponseFormatter
from src.core.logger import log
from src.api.schemas.region import (
    GetCityByNameRequest,
    GetRegionByNameRequest,
    UpdateCityProvinceRequest,
    BatchUpdateCityProvinceRequest,
    CityItemResponse,
    RegionItemResponse,
    ProvinceItemResponse,
    AllProvincesResponse,
    AllCitiesResponse,
    AllRegionsResponse,
    SyncResultResponse
)
from src.api.utils.validators import validate_args, validate_json
from src.api.utils.swagger import create_swagger_spec

# 创建蓝图
region_blueprint = Blueprint('region', __name__, url_prefix='/api/region')

def register_region_blueprint(app):
    """注册区域数据API蓝图"""
    app.register_blueprint(region_blueprint)

# 获取区域管理器实例
region_manager = get_region_manager()


# ============== Swagger 规范定义 ==============

GET_CITY_BY_CODE_SPEC = create_swagger_spec(
    response_schema=CityItemResponse,
    summary="根据城市代码获取城市名称",
    tags=["区域数据"],
    parameters=[{
        'name': 'city_code',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': '城市代码'
    }]
)

GET_CITY_BY_NAME_SPEC = create_swagger_spec(
    request_schema=GetCityByNameRequest,
    response_schema=CityItemResponse,
    summary="根据城市名称获取城市代码",
    tags=["区域数据"],
    request_in="query"
)

GET_REGION_BY_CODE_SPEC = create_swagger_spec(
    response_schema=RegionItemResponse,
    summary="根据区域代码获取区域信息",
    tags=["区域数据"],
    parameters=[{
        'name': 'region_code',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': '区域代码'
    }]
)

GET_REGION_BY_NAME_SPEC = create_swagger_spec(
    request_schema=GetRegionByNameRequest,
    response_schema=RegionItemResponse,
    summary="根据区域名称获取区域代码",
    tags=["区域数据"],
    request_in="query"
)

GET_PROVINCE_REGION_SPEC = create_swagger_spec(
    response_schema=RegionItemResponse,
    summary="获取省份所属的大区",
    tags=["区域数据"],
    parameters=[{
        'name': 'province_code',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': '省份代码'
    }]
)

GET_REGION_PROVINCES_SPEC = create_swagger_spec(
    summary="获取大区下属的所有省份",
    tags=["区域数据"],
    parameters=[{
        'name': 'name',
        'in': 'query',
        'type': 'string',
        'required': True,
        'description': '大区名称'
    }]
)

GET_REGION_CHILDREN_SPEC = create_swagger_spec(
    summary="获取区域的直接子区域",
    tags=["区域数据"],
    parameters=[{
        'name': 'parent_code',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': '父级区域代码'
    }]
)

GET_REGION_ALL_CHILDREN_SPEC = create_swagger_spec(
    summary="获取区域的所有子区域（递归）",
    tags=["区域数据"],
    parameters=[{
        'name': 'parent_code',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': '父级区域代码'
    }]
)

GET_REGION_PATH_SPEC = create_swagger_spec(
    summary="获取区域的完整路径",
    description="从顶级区域到当前区域的完整路径",
    tags=["区域数据"],
    parameters=[{
        'name': 'region_code',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': '区域代码'
    }]
)

SYNC_REGION_DATA_SPEC = create_swagger_spec(
    response_schema=SyncResultResponse,
    summary="手动触发区域数据同步到Redis",
    tags=["区域数据"]
)

GET_ALL_PROVINCES_SPEC = create_swagger_spec(
    response_schema=AllProvincesResponse,
    summary="获取所有省份数据",
    tags=["区域数据"]
)

GET_ALL_CITIES_SPEC = create_swagger_spec(
    response_schema=AllCitiesResponse,
    summary="获取所有城市数据",
    tags=["区域数据"]
)

GET_ALL_REGIONS_SPEC = create_swagger_spec(
    response_schema=AllRegionsResponse,
    summary="获取所有区域关系数据",
    tags=["区域数据"]
)

GET_PROVINCE_CITIES_SPEC = create_swagger_spec(
    summary="获取各省份下属的城市列表",
    tags=["区域数据"],
    parameters=[{
        'name': 'province_code',
        'in': 'query',
        'type': 'string',
        'required': False,
        'description': '省份代码（可选，不传则返回全部）'
    }]
)

SYNC_PROVINCE_CITIES_SPEC = create_swagger_spec(
    response_schema=SyncResultResponse,
    summary="手动触发同步各省份下属城市数据到Redis",
    tags=["区域数据"]
)

UPDATE_CITY_PROVINCE_SPEC = create_swagger_spec(
    request_schema=UpdateCityProvinceRequest,
    summary="更新城市的所属省份信息",
    tags=["区域数据"],
    request_in="body"
)

BATCH_UPDATE_CITY_PROVINCE_SPEC = create_swagger_spec(
    request_schema=BatchUpdateCityProvinceRequest,
    summary="批量更新城市的所属省份信息",
    tags=["区域数据"],
    request_in="body"
)

SYNC_CITY_PROVINCE_SPEC = create_swagger_spec(
    response_schema=SyncResultResponse,
    summary="同步城市的所属省份信息",
    description="根据region_children表同步城市省份归属",
    tags=["区域数据"]
)


# ============== API 端点 ==============


@region_blueprint.route('/city/code/<city_code>', methods=['GET'])
@swag_from(GET_CITY_BY_CODE_SPEC)
def get_city_name_by_code(city_code):
    """根据城市代码获取城市名称"""
    city_name = region_manager.get_city_name_by_code(city_code)
    
    if not city_name:
        return jsonify(ResponseFormatter.error(
            ResponseCode.DATA_NOT_FOUND,
            f"城市代码 {city_code} 不存在"
        )), 404
    
    return jsonify(ResponseFormatter.success({
        'city_code': city_code,
        'city_name': city_name
    }))

@region_blueprint.route('/city/name', methods=['GET'])
@swag_from(GET_CITY_BY_NAME_SPEC)
@validate_args(GetCityByNameRequest)
def get_city_code_by_name(validated_data: GetCityByNameRequest):
    """根据城市名称获取城市代码（查询参数版本）"""
    city_name = validated_data.name
    return get_city_code_by_name_impl(city_name)

def get_city_code_by_name_impl(city_name):
    """城市名称查询的实际实现"""
    log.info(f"查询城市名称: {city_name}")
    city_code = region_manager.get_city_code_by_name(city_name)
    
    if not city_code:
        return jsonify(ResponseFormatter.error(
            ResponseCode.DATA_NOT_FOUND,
            f"城市名称 {city_name} 不存在"
        )), 404
    
    return jsonify(ResponseFormatter.success({
        'city_code': city_code,
        'city_name': city_name
    }))


@region_blueprint.route('/code/<region_code>', methods=['GET'])
@swag_from(GET_REGION_BY_CODE_SPEC)
def get_region_by_code(region_code):
    """根据区域代码获取区域信息"""
    region_info = region_manager.get_region_by_code(region_code)
    
    if not region_info:
        return jsonify(ResponseFormatter.error(
            ResponseCode.DATA_NOT_FOUND,
            f"区域代码 {region_code} 不存在"
        )), 404
    
    return jsonify(ResponseFormatter.success(region_info))

@region_blueprint.route('/name', methods=['GET'])
@swag_from(GET_REGION_BY_NAME_SPEC)
@validate_args(GetRegionByNameRequest)
def get_region_code_by_name(validated_data: GetRegionByNameRequest):
    """根据区域名称获取区域代码"""
    region_name = validated_data.name
    level = validated_data.level
    
    region_code = region_manager.get_region_code_by_name(region_name, level)
    
    if not region_code:
        return jsonify(ResponseFormatter.error(
            ResponseCode.DATA_NOT_FOUND,
            f"区域名称 {region_name} {'（层级: ' + str(level) + '）' if level else ''} 不存在"
        )), 404
    
    return jsonify(ResponseFormatter.success({
        'region_code': region_code,
        'region_name': region_name
    }))

@region_blueprint.route('/province/region/<province_code>', methods=['GET'])
@swag_from(GET_PROVINCE_REGION_SPEC)
def get_province_region(province_code):
    """获取省份所属的大区"""
    region_name = region_manager.get_province_region(province_code)
    
    if not region_name:
        return jsonify(ResponseFormatter.error(
            ResponseCode.DATA_NOT_FOUND,
            f"省份代码 {province_code} 不存在或没有所属大区"
        )), 404
    
    return jsonify(ResponseFormatter.success({
        'province_code': province_code,
        'region_name': region_name
    }))


@region_blueprint.route('/region/provinces', methods=['GET'])
@swag_from(GET_REGION_PROVINCES_SPEC)
def get_region_provinces():
    """获取大区下属的所有省份（查询参数版本）"""
    region_name = request.args.get('region')
    
    if not region_name:
        return jsonify(ResponseFormatter.error(
            ResponseCode.PARAM_ERROR,
            "缺少必要参数: region"
        )), 400
    
    return get_region_provinces_impl(region_name)

def get_region_provinces_impl(region_name):
    """大区省份查询的实际实现"""
    try:
        log.info(f"查询大区: {region_name} 的所有省份")
        
        provinces = region_manager.get_region_provinces(region_name)
        
        if not provinces:
            log.warning(f"大区 {region_name} 不存在或没有下属省份")
            return jsonify(ResponseFormatter.error(
                ResponseCode.DATA_NOT_FOUND,
                f"大区 {region_name} 不存在或没有下属省份"
            )), 404
        
        log.info(f"成功获取大区 {region_name} 的 {len(provinces)} 个省份")
        return jsonify(ResponseFormatter.success({
            'region_name': region_name,
            'provinces': provinces
        }))
    except Exception as e:
        log.error(f"获取大区省份失败: {e}")
        return jsonify(ResponseFormatter.error(
            ResponseCode.SERVER_ERROR,
            f"获取大区省份时发生错误"
        )), 500

@region_blueprint.route('/children/<parent_code>', methods=['GET'])
@swag_from(GET_REGION_CHILDREN_SPEC)
def get_region_children(parent_code):
    """获取区域的直接子区域"""
    children = region_manager.get_region_children(parent_code)
    
    return jsonify(ResponseFormatter.success({
        'parent_code': parent_code,
        'children': children
    }))

@region_blueprint.route('/all-children/<parent_code>', methods=['GET'])
@swag_from(GET_REGION_ALL_CHILDREN_SPEC)
def get_region_all_children(parent_code):
    """获取区域的所有子区域（递归）"""
    all_children = region_manager.get_region_all_children(parent_code)
    
    return jsonify(ResponseFormatter.success({
        'parent_code': parent_code,
        'children_count': len(all_children),
        'children': all_children
    }))

@region_blueprint.route('/path/<region_code>', methods=['GET'])
@swag_from(GET_REGION_PATH_SPEC)
def get_region_path(region_code):
    """获取区域的完整路径（从顶级区域到当前区域）"""
    region_info = region_manager.get_region_by_code(region_code)
    
    if not region_info:
        return jsonify(ResponseFormatter.error(
            ResponseCode.DATA_NOT_FOUND,
            f"区域代码 {region_code} 不存在"
        )), 404
    
    path = region_manager.get_region_path(region_code)
    
    return jsonify(ResponseFormatter.success({
        'region_code': region_code,
        'path': path
    }))

@region_blueprint.route('/sync', methods=['POST'])
@swag_from(SYNC_REGION_DATA_SPEC)
def sync_region_data():
    """手动触发区域数据同步到Redis"""
    success = region_manager.sync_to_redis()
    
    if not success:
        return jsonify(ResponseFormatter.error(
            ResponseCode.SERVER_ERROR,
            "同步区域数据到Redis失败"
        )), 500
    
    return jsonify(ResponseFormatter.success({
        'success': True
    }, "区域数据同步到Redis成功"))

@region_blueprint.route('/provinces', methods=['GET'])
@swag_from(GET_ALL_PROVINCES_SPEC)
def get_all_provinces():
    """获取所有省份数据"""
    provinces = region_manager.get_all_provinces()
    return jsonify(ResponseFormatter.success({
        'provinces': provinces
    }))

@region_blueprint.route('/cities', methods=['GET'])
@swag_from(GET_ALL_CITIES_SPEC)
def get_all_cities():
    """获取所有城市数据"""
    cities = region_manager.get_all_cities()
    return jsonify(ResponseFormatter.success({
        'cities': cities
    }))

@region_blueprint.route('/regions', methods=['GET'])
@swag_from(GET_ALL_REGIONS_SPEC)
def get_all_regions():
    """获取所有区域关系数据"""
    regions = region_manager.get_all_regions()
    return jsonify(ResponseFormatter.success({
        'regions': regions
    }))

@region_blueprint.route('/province/cities', methods=['GET'])
@swag_from(GET_PROVINCE_CITIES_SPEC)
def get_province_cities():
    """获取各省份下属的城市列表"""
    province_code = request.args.get('province_code')
    
    # 获取省份城市数据
    province_cities = region_manager.get_province_cities(province_code)
    
    return jsonify(ResponseFormatter.success({
        'provinces': province_cities
    }))

@region_blueprint.route('/sync_province_cities', methods=['POST'])
@swag_from(SYNC_PROVINCE_CITIES_SPEC)
def sync_province_cities():
    """手动触发同步各省份下属城市数据到Redis"""
    success = region_manager.sync_province_cities()
    
    if not success:
        return jsonify(ResponseFormatter.error(
            ResponseCode.SERVER_ERROR,
            "同步省份城市数据到Redis失败"
        )), 500
    
    return jsonify(ResponseFormatter.success({
        'success': True
    }, "省份城市数据同步到Redis成功"))

@region_blueprint.route('/update_city_province', methods=['POST'])
@swag_from(UPDATE_CITY_PROVINCE_SPEC)
def update_city_province():
    """更新城市的所属省份信息"""
    data = request.get_json()
    
    if not data:
        return jsonify(ResponseFormatter.error(
            ResponseCode.PARAM_ERROR,
            "请求体为空"
        )), 400
    
    city_code = data.get('city_code')
    province_code = data.get('province_code')
    
    if not city_code or not province_code:
        return jsonify(ResponseFormatter.error(
            ResponseCode.PARAM_ERROR,
            "缺少必要参数: city_code 或 province_code"
        )), 400
    
    # 如果没有提供省份名称，则尝试从数据库获取
    province_name = data.get('province_name')
    if not province_name:
        # 从省份信息中查找
        province_info = region_manager.get_region_by_code(province_code)
        if province_info:
            province_name = province_info.get('name')
    
    result = region_manager.update_city_province(city_code, province_code, province_name)
    
    if not result:
        return jsonify(ResponseFormatter.error(
            ResponseCode.DATA_NOT_FOUND,
            f"更新失败，城市代码 {city_code} 或省份代码 {province_code} 不存在"
        )), 404
    
    return jsonify(ResponseFormatter.success({
        'city_code': city_code,
        'province_code': province_code,
        'province_name': province_name,
        'success': True
    }, "更新城市所属省份信息成功"))


@region_blueprint.route('/batch_update_city_province', methods=['POST'])
@swag_from(BATCH_UPDATE_CITY_PROVINCE_SPEC)
def batch_update_city_province():
    """批量更新城市的所属省份信息"""
    data = request.get_json()
    
    if not data or 'cities' not in data:
        return jsonify(ResponseFormatter.error(
            ResponseCode.PARAM_ERROR,
            "缺少必要参数: cities"
        )), 400
    
    cities = data.get('cities', [])
    if not isinstance(cities, list) or len(cities) == 0:
        return jsonify(ResponseFormatter.error(
            ResponseCode.PARAM_ERROR,
            "cities 必须是非空数组"
        )), 400
    
    success_count = 0
    failed_count = 0
    
    for city_data in cities:
        city_code = city_data.get('city_code')
        province_code = city_data.get('province_code')
        province_name = city_data.get('province_name')
        
        if not city_code or not province_code:
            failed_count += 1
            continue
            
        # 如果没有提供省份名称，则尝试从数据库获取
        if not province_name:
            province_info = region_manager.get_region_by_code(province_code)
            if province_info:
                province_name = province_info.get('name')
        
        result = region_manager.update_city_province(city_code, province_code, province_name)
        
        if result:
            success_count += 1
        else:
            failed_count += 1
    
    return jsonify(ResponseFormatter.success({
        'total': len(cities),
        'success_count': success_count,
        'failed_count': failed_count
    }, f"批量更新城市所属省份信息完成，成功: {success_count}，失败: {failed_count}"))

@region_blueprint.route('/sync_city_province', methods=['POST'])
@swag_from(SYNC_CITY_PROVINCE_SPEC)
def sync_city_province():
    """同步城市的所属省份信息（根据region_children表）"""
    try:
        result = region_manager.sync_city_province()
        
        if result:
            total, success_count, failed_count = result
            return jsonify(ResponseFormatter.success({
                'total': total,
                'success_count': success_count,
                'failed_count': failed_count
            }, f"同步城市所属省份信息完成，成功: {success_count}，失败: {failed_count}"))
        else:
            return jsonify(ResponseFormatter.error(
                ResponseCode.SERVER_ERROR,
                "同步城市所属省份信息失败"
            )), 500
    except Exception as e:
        log.error(f"同步城市所属省份信息失败: {e}")
        return jsonify(ResponseFormatter.error(
            ResponseCode.SERVER_ERROR,
            f"同步城市所属省份信息失败: {str(e)}"
        )), 500
