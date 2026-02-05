"""
关键词检查API控制器
提供关键词检查的HTTP接口
"""
from flask import Blueprint, request, jsonify
from flasgger import swag_from

from src.core.logger import log
from src.core.constants.respond import ResponseCode, ResponseFormatter
from src.engine.spider.word_check_spider import word_check_spider

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
def check_words():
    """检查关键词是否存在"""
    try:
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "请求参数为空"))
        
        # 验证必要参数
        words = data.get('words')
        if not words:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: words"))
        
        # 验证参数类型
        if not isinstance(words, list):
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "参数 words 必须是数组"))
        
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
def check_single_word():
    """检查单个关键词是否存在"""
    try:
        # 获取请求参数
        word = request.args.get('word')
        if not word:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: word"))
        
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