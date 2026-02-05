"""
请求校验工具模块
提供 Pydantic Schema 校验装饰器，用于 Controller 层自动化请求验证
"""
import functools
from flask import request, jsonify, g
from pydantic import BaseModel, ValidationError
from typing import Type, Optional
from src.core.constants.respond import ResponseCode, ResponseFormatter


def validate_request(schema: Type[BaseModel], source: str = "json", inject_as_arg: bool = True):
    """
    请求校验装饰器
    
    参数:
        schema: Pydantic Schema 类
        source: 数据来源，支持 "json"（请求体）或 "args"（查询参数）
        inject_as_arg: 是否将校验数据作为第一个参数注入（True）还是存入 flask.g（False）
    
    使用示例（注入参数模式）:
        @validate_json(CreateTaskRequest)
        def create_task(validated_data: CreateTaskRequest):
            pass
    
    使用示例（flask.g 模式，兼容 @with_cookie_manager 等现有装饰器）:
        @with_cookie_manager
        @validate_json(AddCookieRequest, inject_as_arg=False)
        def add_cookie(cookie_manager):
            validated_data = g.validated_data
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # 根据来源获取数据
                if source == "json":
                    data = request.get_json(silent=True) or {}
                elif source == "args":
                    data = request.args.to_dict()
                else:
                    data = {}
                
                # 使用 Pydantic 进行校验
                if hasattr(schema, 'model_validate'):
                    validated = schema.model_validate(data)
                else:
                    validated = schema(**data)
                
                if inject_as_arg:
                    # 将校验后的数据作为第一个参数传递给被装饰的函数
                    return func(validated, *args, **kwargs)
                else:
                    # 存入 flask.g，供被装饰函数内部访问
                    g.validated_data = validated
                    return func(*args, **kwargs)
                
            except ValidationError as e:
                # 格式化 Pydantic 校验错误
                errors = []
                for error in e.errors():
                    field = ".".join(str(loc) for loc in error["loc"])
                    msg = error["msg"]
                    errors.append(f"{field}: {msg}")
                
                error_msg = "请求参数校验失败: " + "; ".join(errors)
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, error_msg))
                
            except Exception as e:
                return jsonify(ResponseFormatter.error(
                    ResponseCode.SERVER_ERROR, 
                    f"请求处理失败: {str(e)}"
                ))
        
        return wrapper
    return decorator


def validate_json(schema: Type[BaseModel], inject_as_arg: bool = True):
    """
    JSON 请求体校验装饰器（简写）
    """
    return validate_request(schema, source="json", inject_as_arg=inject_as_arg)


def validate_args(schema: Type[BaseModel], inject_as_arg: bool = True):
    """
    查询参数校验装饰器（简写）
    """
    return validate_request(schema, source="args", inject_as_arg=inject_as_arg)

