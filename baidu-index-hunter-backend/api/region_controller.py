#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
区域数据API控制器
提供百度指数区域代码相关的API接口
"""

from flask import Blueprint, request, jsonify
from flasgger import swag_from
from region_manager.region_manager import get_region_manager
from constant.respond import ResponseCode, ResponseFormatter
from utils.logger import log

# 创建蓝图
region_blueprint = Blueprint('region', __name__, url_prefix='/api/region')

def register_region_blueprint(app):
    """注册区域数据API蓝图"""
    app.register_blueprint(region_blueprint)

# 获取区域管理器实例
region_manager = get_region_manager()

@region_blueprint.route('/city/code/<city_code>', methods=['GET'])
@swag_from({
    'tags': ['区域数据'],
    'summary': '根据城市代码获取城市名称',
    'parameters': [
        {
            'name': 'city_code',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '城市代码'
        }
    ],
    'responses': {
        '200': {
            'description': '成功获取城市名称',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'city_code': {'type': 'string'},
                            'city_name': {'type': 'string'}
                        }
                    }
                }
            }
        },
        '404': {
            'description': '城市代码不存在',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10500},
                    'msg': {'type': 'string', 'example': '数据不存在'},
                    'data': {'type': 'null'}
                }
            }
        }
    }
})
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
@swag_from({
    'tags': ['区域数据'],
    'summary': '根据城市名称获取城市代码',
    'parameters': [
        {
            'name': 'name',
            'in': 'query',
            'type': 'string',
            'required': True,
            'description': '城市名称'
        }
    ],
    'responses': {
        '200': {
            'description': '成功获取城市代码',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'city_code': {'type': 'string'},
                            'city_name': {'type': 'string'}
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
        '404': {
            'description': '城市名称不存在',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10500},
                    'msg': {'type': 'string', 'example': '数据不存在'},
                    'data': {'type': 'null'}
                }
            }
        }
    }
})
def get_city_code_by_name():
    """根据城市名称获取城市代码（查询参数版本）"""
    city_name = request.args.get('name')
    
    if not city_name:
        return jsonify(ResponseFormatter.error(
            ResponseCode.PARAM_ERROR,
            "缺少必要参数: name"
        )), 400
    
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
@swag_from({
    'tags': ['区域数据'],
    'summary': '根据区域代码获取区域信息',
    'parameters': [
        {
            'name': 'region_code',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '区域代码'
        }
    ],
    'responses': {
        '200': {
            'description': '成功获取区域信息',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'code': {'type': 'string'},
                            'name': {'type': 'string'},
                            'level': {'type': 'integer'},
                            'parent_code': {'type': 'string'}
                        }
                    }
                }
            }
        },
        '404': {
            'description': '区域代码不存在',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10500},
                    'msg': {'type': 'string', 'example': '数据不存在'},
                    'data': {'type': 'null'}
                }
            }
        }
    }
})
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
@swag_from({
    'tags': ['区域数据'],
    'summary': '根据区域名称获取区域代码',
    'parameters': [
        {
            'name': 'name',
            'in': 'query',
            'type': 'string',
            'required': True,
            'description': '区域名称'
        },
        {
            'name': 'level',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'description': '区域层级（1-省级，2-地级市，3-区县级，4-更细分级）'
        }
    ],
    'responses': {
        '200': {
            'description': '成功获取区域代码',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'region_code': {'type': 'string'},
                            'region_name': {'type': 'string'}
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
        '404': {
            'description': '区域名称不存在',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10500},
                    'msg': {'type': 'string', 'example': '数据不存在'},
                    'data': {'type': 'null'}
                }
            }
        }
    }
})
def get_region_code_by_name():
    """根据区域名称获取区域代码"""
    region_name = request.args.get('name')
    level = request.args.get('level')
    
    if not region_name:
        return jsonify(ResponseFormatter.error(
            ResponseCode.PARAM_ERROR,
            "缺少必要参数: name"
        )), 400
    
    # 将level转换为整数或None
    if level and level.strip():
        try:
            level = int(level)
        except ValueError:
            return jsonify(ResponseFormatter.error(
                ResponseCode.PARAM_ERROR,
                "参数 level 必须是整数"
            )), 400
    else:
        level = None
    
    region_code = region_manager.get_region_code_by_name(region_name, level)
    
    if not region_code:
        return jsonify(ResponseFormatter.error(
            ResponseCode.DATA_NOT_FOUND,
            f"区域名称 {region_name} {'(层级: ' + str(level) + ')' if level else ''} 不存在"
        )), 404
    
    return jsonify(ResponseFormatter.success({
        'region_code': region_code,
        'region_name': region_name
    }))

@region_blueprint.route('/province/region/<province_code>', methods=['GET'])
@swag_from({
    'tags': ['区域数据'],
    'summary': '获取省份所属的大区',
    'parameters': [
        {
            'name': 'province_code',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '省份代码'
        }
    ],
    'responses': {
        '200': {
            'description': '成功获取省份所属大区',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'province_code': {'type': 'string'},
                            'region_name': {'type': 'string'}
                        }
                    }
                }
            }
        },
        '404': {
            'description': '省份代码不存在或没有所属大区',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10500},
                    'msg': {'type': 'string', 'example': '数据不存在'},
                    'data': {'type': 'null'}
                }
            }
        }
    }
})
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
@swag_from({
    'tags': ['区域数据'],
    'summary': '获取大区下属的所有省份',
    'parameters': [
        {
            'name': 'region',
            'in': 'query',
            'type': 'string',
            'required': True,
            'description': '大区名称（华东、华北等）'
        }
    ],
    'responses': {
        '200': {
            'description': '成功获取大区下属省份',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'region_name': {'type': 'string'},
                            'provinces': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'code': {'type': 'string'},
                                        'name': {'type': 'string'},
                                        'level': {'type': 'integer'}
                                    }
                                }
                            }
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
        '404': {
            'description': '大区名称不存在或没有下属省份',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10500},
                    'msg': {'type': 'string', 'example': '数据不存在'},
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
@swag_from({
    'tags': ['区域数据'],
    'summary': '获取区域的直接子区域',
    'parameters': [
        {
            'name': 'parent_code',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '父区域代码'
        }
    ],
    'responses': {
        '200': {
            'description': '成功获取子区域',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'parent_code': {'type': 'string'},
                            'children': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'code': {'type': 'string'},
                                        'name': {'type': 'string'},
                                        'level': {'type': 'integer'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
})
def get_region_children(parent_code):
    """获取区域的直接子区域"""
    children = region_manager.get_region_children(parent_code)
    
    return jsonify(ResponseFormatter.success({
        'parent_code': parent_code,
        'children': children
    }))

@region_blueprint.route('/all-children/<parent_code>', methods=['GET'])
@swag_from({
    'tags': ['区域数据'],
    'summary': '获取区域的所有子区域（递归）',
    'parameters': [
        {
            'name': 'parent_code',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '父区域代码'
        }
    ],
    'responses': {
        '200': {
            'description': '成功获取所有子区域',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'parent_code': {'type': 'string'},
                            'children_count': {'type': 'integer'},
                            'children': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'code': {'type': 'string'},
                                        'name': {'type': 'string'},
                                        'level': {'type': 'integer'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
})
def get_region_all_children(parent_code):
    """获取区域的所有子区域（递归）"""
    all_children = region_manager.get_region_all_children(parent_code)
    
    return jsonify(ResponseFormatter.success({
        'parent_code': parent_code,
        'children_count': len(all_children),
        'children': all_children
    }))

@region_blueprint.route('/path/<region_code>', methods=['GET'])
@swag_from({
    'tags': ['区域数据'],
    'summary': '获取区域的完整路径（从顶级区域到当前区域）',
    'parameters': [
        {
            'name': 'region_code',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '区域代码'
        }
    ],
    'responses': {
        '200': {
            'description': '成功获取区域路径',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'region_code': {'type': 'string'},
                            'path': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'code': {'type': 'string'},
                                        'name': {'type': 'string'},
                                        'level': {'type': 'integer'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        '404': {
            'description': '区域代码不存在',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10500},
                    'msg': {'type': 'string', 'example': '数据不存在'},
                    'data': {'type': 'null'}
                }
            }
        }
    }
})
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
@swag_from({
    'tags': ['区域数据'],
    'summary': '手动触发区域数据同步到Redis',
    'responses': {
        '200': {
            'description': '同步成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'success': {'type': 'boolean'}
                        }
                    }
                }
            }
        },
        '500': {
            'description': '同步失败',
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
@swag_from({
    'tags': ['区域数据'],
    'summary': '获取所有省份数据',
    'responses': {
        '200': {
            'description': '成功获取所有省份数据',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'provinces': {
                                'type': 'object',
                                'additionalProperties': {
                                    'type': 'object',
                                    'properties': {
                                        'code': {'type': 'string'},
                                        'name': {'type': 'string'},
                                        'region': {'type': 'string'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
})
def get_all_provinces():
    """获取所有省份数据"""
    provinces = region_manager.get_all_provinces()
    return jsonify(ResponseFormatter.success({
        'provinces': provinces
    }))

@region_blueprint.route('/cities', methods=['GET'])
@swag_from({
    'tags': ['区域数据'],
    'summary': '获取所有城市数据',
    'responses': {
        '200': {
            'description': '成功获取所有城市数据',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'cities': {
                                'type': 'object',
                                'additionalProperties': {
                                    'type': 'object',
                                    'properties': {
                                        'code': {'type': 'string'},
                                        'name': {'type': 'string'},
                                        'province_code': {'type': 'string'},
                                        'province_name': {'type': 'string'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
})
def get_all_cities():
    """获取所有城市数据"""
    cities = region_manager.get_all_cities()
    return jsonify(ResponseFormatter.success({
        'cities': cities
    }))

@region_blueprint.route('/regions', methods=['GET'])
@swag_from({
    'tags': ['区域数据'],
    'summary': '获取所有区域关系数据',
    'responses': {
        '200': {
            'description': '成功获取所有区域关系数据',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'regions': {
                                'type': 'object',
                                'additionalProperties': {
                                    'type': 'object',
                                    'properties': {
                                        'code': {'type': 'string'},
                                        'name': {'type': 'string'},
                                        'level': {'type': 'integer'},
                                        'parent_code': {'type': 'string'},
                                        'parent_name': {'type': 'string'},
                                        'children': {
                                            'type': 'array',
                                            'items': {'type': 'string'}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
})
def get_all_regions():
    """获取所有区域关系数据"""
    regions = region_manager.get_all_regions()
    return jsonify(ResponseFormatter.success({
        'regions': regions
    }))

@region_blueprint.route('/province/cities', methods=['GET'])
@swag_from({
    'tags': ['区域数据'],
    'summary': '获取各省份下属的城市列表',
    'parameters': [
        {
            'name': 'province_code',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': '省份代码，如不提供则返回所有省份数据'
        }
    ],
    'responses': {
        '200': {
            'description': '成功获取省份城市列表',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'provinces': {
                                'type': 'object',
                                'additionalProperties': {
                                    'type': 'object',
                                    'properties': {
                                        'province_code': {'type': 'string'},
                                        'province_name': {'type': 'string'},
                                        'city_count': {'type': 'integer'},
                                        'cities': {
                                            'type': 'object',
                                            'additionalProperties': {
                                                'type': 'object',
                                                'properties': {
                                                    'code': {'type': 'string'},
                                                    'name': {'type': 'string'}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
})
def get_province_cities():
    """获取各省份下属的城市列表"""
    province_code = request.args.get('province_code')
    
    # 获取省份城市数据
    province_cities = region_manager.get_province_cities(province_code)
    
    return jsonify(ResponseFormatter.success({
        'provinces': province_cities
    }))

@region_blueprint.route('/sync_province_cities', methods=['POST'])
@swag_from({
    'tags': ['区域数据'],
    'summary': '同步各省份下属城市数据到Redis',
    'responses': {
        '200': {
            'description': '同步成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'success': {'type': 'boolean'}
                        }
                    }
                }
            }
        },
        '500': {
            'description': '同步失败',
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
@swag_from({
    'tags': ['区域数据'],
    'summary': '更新城市的所属省份信息',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'city_code': {'type': 'string', 'description': '城市代码'},
                    'province_code': {'type': 'string', 'description': '省份代码'},
                    'province_name': {'type': 'string', 'description': '省份名称'}
                },
                'required': ['city_code', 'province_code']
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
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'city_code': {'type': 'string'},
                            'province_code': {'type': 'string'},
                            'province_name': {'type': 'string'},
                            'success': {'type': 'boolean'}
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
        '404': {
            'description': '城市或省份不存在',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10500},
                    'msg': {'type': 'string', 'example': '数据不存在'},
                    'data': {'type': 'null'}
                }
            }
        }
    }
})
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
@swag_from({
    'tags': ['区域数据'],
    'summary': '批量更新城市的所属省份信息',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'cities': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'city_code': {'type': 'string', 'description': '城市代码'},
                                'province_code': {'type': 'string', 'description': '省份代码'},
                                'province_name': {'type': 'string', 'description': '省份名称'}
                            },
                            'required': ['city_code', 'province_code']
                        }
                    }
                },
                'required': ['cities']
            }
        }
    ],
    'responses': {
        '200': {
            'description': '批量更新成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'total': {'type': 'integer'},
                            'success_count': {'type': 'integer'},
                            'failed_count': {'type': 'integer'}
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
        }
    }
})
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
@swag_from({
    'tags': ['区域数据'],
    'summary': '同步城市的所属省份信息（根据region_children表）',
    'responses': {
        '200': {
            'description': '同步成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'total': {'type': 'integer'},
                            'success_count': {'type': 'integer'},
                            'failed_count': {'type': 'integer'}
                        }
                    }
                }
            }
        },
        '500': {
            'description': '同步失败',
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
