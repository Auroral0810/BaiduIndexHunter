"""
Swagger 集成工具模块
提供 Pydantic Schema 到 OpenAPI 规范的自动转换
"""
from typing import Type, Dict, Any, List, Optional, get_origin, get_args
from pydantic import BaseModel
from enum import Enum


def pydantic_to_openapi(model: Type[BaseModel]) -> Dict[str, Any]:
    """
    将 Pydantic 模型转换为 OpenAPI Schema 格式
    
    参数:
        model: Pydantic BaseModel 类
    
    返回:
        OpenAPI Schema 字典
    """
    schema = model.model_json_schema()
    return _convert_json_schema_to_openapi(schema)


def _convert_json_schema_to_openapi(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    将 JSON Schema 转换为 OpenAPI 兼容格式
    """
    result = {}
    
    # 处理类型
    if "type" in schema:
        result["type"] = schema["type"]
    
    # 处理 anyOf（Pydantic v2 对 Optional 的处理）
    if "anyOf" in schema:
        # 取第一个非 null 的类型
        for item in schema["anyOf"]:
            if item.get("type") != "null":
                result.update(_convert_json_schema_to_openapi(item))
                break
    
    # 处理属性
    if "properties" in schema:
        result["type"] = "object"
        result["properties"] = {}
        for prop_name, prop_schema in schema["properties"].items():
            result["properties"][prop_name] = _convert_json_schema_to_openapi(prop_schema)
    
    # 处理必填字段
    if "required" in schema:
        result["required"] = schema["required"]
    
    # 处理数组
    if schema.get("type") == "array" and "items" in schema:
        result["items"] = _convert_json_schema_to_openapi(schema["items"])
    
    # 处理描述
    if "description" in schema:
        result["description"] = schema["description"]
    
    # 处理默认值
    if "default" in schema:
        result["default"] = schema["default"]
    
    # 处理示例
    if "example" in schema:
        result["example"] = schema["example"]
    
    # 处理枚举
    if "enum" in schema:
        result["enum"] = schema["enum"]
    
    # 处理标题
    if "title" in schema:
        result["title"] = schema["title"]
    
    # 处理 $defs（Pydantic v2 的定义引用）
    if "$defs" in schema:
        # 展开引用，不使用 $ref
        pass
    
    # 处理 $ref
    if "$ref" in schema:
        # 简单处理：返回 object 类型
        result["type"] = "object"
    
    return result


def create_swagger_spec(
    request_schema: Type[BaseModel] = None,
    response_schema: Type[BaseModel] = None,
    summary: str = "",
    description: str = "",
    tags: List[str] = None,
    parameters: List[Dict] = None,
    request_in: str = "body"
) -> Dict[str, Any]:
    """
    创建 Swagger/OpenAPI 规范字典
    
    参数:
        request_schema: 请求 Pydantic Schema
        response_schema: 响应 Pydantic Schema
        summary: 接口摘要
        description: 接口描述
        tags: 标签列表
        parameters: 额外参数（路径参数等）
        request_in: 请求参数位置 ("body" 或 "query")
    
    返回:
        可用于 @swag_from 的字典
    """
    spec = {
        "summary": summary,
        "description": description,
        "tags": tags or [],
        "parameters": parameters or [],
        "responses": {
            "200": {
                "description": "请求成功",
                "schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer", "example": 10000},
                        "msg": {"type": "string", "example": "请求成功"},
                        "data": {}
                    }
                }
            },
            "400": {
                "description": "参数错误",
                "schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer", "example": 10100},
                        "msg": {"type": "string", "example": "参数错误"},
                        "data": {"type": "null"}
                    }
                }
            },
            "500": {
                "description": "服务器错误",
                "schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer", "example": 10102},
                        "msg": {"type": "string", "example": "服务器内部错误"},
                        "data": {"type": "null"}
                    }
                }
            }
        }
    }
    
    # 处理请求 Schema
    if request_schema:
        request_openapi = pydantic_to_openapi(request_schema)
        
        if request_in == "body":
            spec["parameters"].append({
                "name": "body",
                "in": "body",
                "required": True,
                "schema": request_openapi
            })
        elif request_in == "query":
            # 将 Schema 属性转为查询参数
            if "properties" in request_openapi:
                required_fields = request_openapi.get("required", [])
                for prop_name, prop_schema in request_openapi["properties"].items():
                    param = {
                        "name": prop_name,
                        "in": "query",
                        "required": prop_name in required_fields,
                        "description": prop_schema.get("description", "")
                    }
                    # 映射类型
                    prop_type = prop_schema.get("type", "string")
                    if prop_type == "integer":
                        param["type"] = "integer"
                    elif prop_type == "boolean":
                        param["type"] = "boolean"
                    elif prop_type == "array":
                        param["type"] = "array"
                        param["items"] = prop_schema.get("items", {"type": "string"})
                    else:
                        param["type"] = "string"
                    
                    if "default" in prop_schema:
                        param["default"] = prop_schema["default"]
                    if "enum" in prop_schema:
                        param["enum"] = prop_schema["enum"]
                    
                    spec["parameters"].append(param)
    
    # 处理响应 Schema
    if response_schema:
        response_openapi = pydantic_to_openapi(response_schema)
        spec["responses"]["200"]["schema"]["properties"]["data"] = response_openapi
    
    return spec
