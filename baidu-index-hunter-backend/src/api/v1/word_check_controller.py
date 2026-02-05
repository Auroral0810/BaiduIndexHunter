"""
关键词检查API控制器
提供关键词检查的HTTP接口
"""
from flask import Blueprint, jsonify
from flasgger import swag_from

from src.core.logger import log
from src.core.constants.respond import ResponseCode, ResponseFormatter
from src.services.word_check_service import word_check_service
from src.api.schemas.word_check import (
    CheckWordsRequest, 
    CheckSingleWordRequest,
    CheckWordsResponse,
    CheckSingleWordResponse
)
from src.api.utils.validators import validate_json, validate_args
from src.api.utils.swagger import create_swagger_spec

# 创建蓝图
word_check_blueprint = Blueprint('word_check', __name__, url_prefix='/api/word-check')


# ============== Swagger 规范定义 ==============

CHECK_WORDS_SPEC = create_swagger_spec(
    request_schema=CheckWordsRequest,
    response_schema=CheckWordsResponse,
    summary="检查关键词是否存在",
    description="检查指定的关键词在百度指数中是否存在",
    tags=["关键词检查"],
    request_in="body"
)

CHECK_SINGLE_WORD_SPEC = create_swagger_spec(
    request_schema=CheckSingleWordRequest,
    response_schema=CheckSingleWordResponse,
    summary="检查单个关键词是否存在",
    description="检查单个关键词在百度指数中是否存在",
    tags=["关键词检查"],
    request_in="query"
)


# ============== API 端点 ==============

@word_check_blueprint.route('/check', methods=['POST'])
@swag_from(CHECK_WORDS_SPEC)
@validate_json(CheckWordsRequest)
def check_words(validated_data: CheckWordsRequest):
    """检查关键词是否存在"""
    try:
        # 从校验后的 Schema 对象获取参数
        words = validated_data.words
        
        results = word_check_service.check_words(words)
        
        return jsonify(ResponseFormatter.success({
            'results': results
        }, "关键词检查完成"))
        
    except Exception as e:
        log.error(f"检查关键词失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"检查关键词失败: {str(e)}"))


@word_check_blueprint.route('/check-single', methods=['GET'])
@swag_from(CHECK_SINGLE_WORD_SPEC)
@validate_args(CheckSingleWordRequest)
def check_single_word(validated_data: CheckSingleWordRequest):
    """检查单个关键词是否存在"""
    try:
        # 从校验后的 Schema 对象获取参数
        word = validated_data.word
        
        result = word_check_service.check_single_word(word)
        
        return jsonify(ResponseFormatter.success(result, "关键词检查完成"))
        
    except Exception as e:
        log.error(f"检查关键词失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"检查关键词失败: {str(e)}"))


def register_word_check_blueprint(app):
    """注册关键词检查蓝图"""
    app.register_blueprint(word_check_blueprint)