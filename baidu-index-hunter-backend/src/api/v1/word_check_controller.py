"""
关键词检查API控制器
提供关键词检查的HTTP接口
"""
from flask import Blueprint, request, jsonify
from flasgger import swag_from

from src.core.logger import log
from src.core.constants.respond import ResponseCode, ResponseFormatter
from src.engine.spider.word_check_spider import word_check_spider
from src.api.schemas.word_check import CheckWordsRequest, CheckSingleWordRequest
from src.api.utils.validators import validate_json, validate_args

# 创建蓝图
word_check_blueprint = Blueprint('word_check', __name__, url_prefix='/api/word-check')


@word_check_blueprint.route('/check', methods=['POST'])
@swag_from({
    'tags': ['关键词检查'],
    'summary': '检查关键词是否存在',
    'description': '检查指定的关键词在百度指数中是否存在',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['words'],
                'properties': {
                    'words': {
                        'type': 'array',
                        'items': {
                            'type': 'string'
                        },
                        'description': '要检查的关键词列表'
                    }
                }
            }
        }
    ],
    'responses': {
        '200': {
            'description': '检查成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'results': {
                                'type': 'object',
                                'additionalProperties': {
                                    'type': 'object',
                                    'properties': {
                                        'exists': {'type': 'boolean'},
                                        'error': {'type': 'string'}
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
@validate_json(CheckWordsRequest)
def check_words(validated_data: CheckWordsRequest):
    """检查关键词是否存在"""
    try:
        # 从校验后的 Schema 对象获取参数
        words = validated_data.words
        
        # 检查关键词
        log.info(f"开始检查 {len(words)} 个关键词")
        results = word_check_spider.check_words_batch(words)
        
        # 处理结果，移除response字段
        clean_results = {}
        for word, result in results.items():
            clean_results[word] = {
                'exists': result.get('exists', False),
            }
            if 'error' in result:
                clean_results[word]['error'] = result['error']
        
        return jsonify(ResponseFormatter.success({
            'results': clean_results
        }, "关键词检查完成"))
        
    except Exception as e:
        log.error(f"检查关键词失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"检查关键词失败: {str(e)}"))


@word_check_blueprint.route('/check-single', methods=['GET'])
@swag_from({
    'tags': ['关键词检查'],
    'summary': '检查单个关键词是否存在',
    'description': '检查单个关键词在百度指数中是否存在',
    'parameters': [
        {
            'name': 'word',
            'in': 'query',
            'type': 'string',
            'required': True,
            'description': '要检查的关键词'
        }
    ],
    'responses': {
        '200': {
            'description': '检查成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer', 'example': 10000},
                    'msg': {'type': 'string', 'example': '请求成功'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'word': {'type': 'string'},
                            'exists': {'type': 'boolean'},
                            'error': {'type': 'string'}
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
@validate_args(CheckSingleWordRequest)
def check_single_word(validated_data: CheckSingleWordRequest):
    """检查单个关键词是否存在"""
    try:
        # 从校验后的 Schema 对象获取参数
        word = validated_data.word
        
        # 检查关键词
        log.info(f"检查关键词: {word}")
        result = word_check_spider.check_word(word)
        
        # 处理结果，移除response字段
        clean_result = {
            'word': word,
            'exists': result.get('exists', False)
        }
        if 'error' in result:
            clean_result['error'] = result['error']
        
        return jsonify(ResponseFormatter.success(clean_result, "关键词检查完成"))
        
    except Exception as e:
        log.error(f"检查关键词失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"检查关键词失败: {str(e)}"))


def register_word_check_blueprint(app):
    """注册关键词检查蓝图"""
    app.register_blueprint(word_check_blueprint)