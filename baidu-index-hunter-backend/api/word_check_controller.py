"""
关键词检查API控制器
提供关键词检查的HTTP接口

流程：
1. 前端发送要检查的关键词列表
2. 后端先从 Redis 缓存中查找已检查过的关键词
3. 对于未检查过的关键词，使用 Scrapy 异步请求百度 API
4. 将结果保存到 Redis 缓存
5. 返回所有关键词的检查结果
"""
import os
import sys
import json
import time
import redis
from datetime import datetime
from flask import Blueprint, request, jsonify
from flasgger import swag_from

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import log
from constant.respond import ResponseCode, ResponseFormatter
from scheduler.task_scheduler import task_scheduler
from core.config import config

# 创建蓝图
word_check_blueprint = Blueprint('word_check', __name__, url_prefix='/api/word-check')

# Redis 键前缀
REDIS_KEY_PREFIX = "baidu_index:word_check:"
# 缓存过期时间（7天）
REDIS_CACHE_EXPIRE = 60 * 60 * 24 * 7


def get_redis_client():
    """获取 Redis 客户端"""
    redis_config = config.redis_config
    return redis.Redis(
        host=redis_config.get('host', 'localhost'),
        port=redis_config.get('port', 6379),
        db=redis_config.get('db', 0),
        password=redis_config.get('password'),
        decode_responses=True
    )


def check_words_from_cache(words: list, redis_client) -> dict:
    """
    从 Redis 缓存中检查关键词
    
    Args:
        words: 关键词列表
        redis_client: Redis 客户端
        
    Returns:
        dict: {keyword: {'exists': bool, 'cached': True}, ...}
    """
    cached_results = {}
    
    for word in words:
        redis_key = f"{REDIS_KEY_PREFIX}{word}"
        cached_data = redis_client.get(redis_key)
        
        if cached_data:
            try:
                data = json.loads(cached_data)
                cached_results[word] = {
                    'exists': data.get('exists', False),
                    'cached': True,
                    'checked_at': data.get('checked_at')
                }
            except json.JSONDecodeError:
                pass
    
    return cached_results


def wait_for_task_results(task_id: str, words: list, redis_client, timeout: int = 30) -> dict:
    """
    等待 Scrapy 任务完成并获取结果
    
    Args:
        task_id: 任务 ID
        words: 待检查的关键词列表
        redis_client: Redis 客户端
        timeout: 超时时间（秒）
        
    Returns:
        dict: {keyword: {'exists': bool}, ...}
    """
    task_result_key = f"baidu_index:word_check_task:{task_id}"
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # 检查任务结果
        results = redis_client.hgetall(task_result_key)
        
        # 如果所有关键词都有结果了
        if len(results) >= len(words):
            final_results = {}
            for word, result_json in results.items():
                try:
                    result = json.loads(result_json)
                    final_results[word] = {
                        'exists': result.get('exists', False)
                    }
                    if result.get('error'):
                        final_results[word]['error'] = result.get('error')
                except json.JSONDecodeError:
                    final_results[word] = {'exists': False, 'error': 'parse_error'}
            return final_results
        
        # 检查任务状态
        task_info = task_scheduler.get_task(task_id)
        if task_info and task_info.get('status') in ['completed', 'failed', 'cancelled']:
            # 任务已结束，返回已有结果
            final_results = {}
            for word, result_json in results.items():
                try:
                    result = json.loads(result_json)
                    final_results[word] = {
                        'exists': result.get('exists', False)
                    }
                    if result.get('error'):
                        final_results[word]['error'] = result.get('error')
                except json.JSONDecodeError:
                    final_results[word] = {'exists': False, 'error': 'parse_error'}
            
            # 对于没有结果的关键词，标记为检查失败
            for word in words:
                if word not in final_results:
                    final_results[word] = {'exists': False, 'error': 'task_failed'}
            
            return final_results
        
        # 等待一小段时间再检查
        time.sleep(0.3)
    
    # 超时，返回已有结果
    results = redis_client.hgetall(task_result_key)
    final_results = {}
    for word, result_json in results.items():
        try:
            result = json.loads(result_json)
            final_results[word] = {'exists': result.get('exists', False)}
        except json.JSONDecodeError:
            final_results[word] = {'exists': False, 'error': 'parse_error'}
    
    # 对于没有结果的关键词，标记为超时
    for word in words:
        if word not in final_results:
            final_results[word] = {'exists': False, 'error': 'timeout'}
    
    return final_results


@word_check_blueprint.route('/check', methods=['POST'])
@swag_from({
    'tags': ['关键词检查'],
    'summary': '检查关键词是否存在',
    'description': '检查指定的关键词在百度指数中是否存在，支持批量检查。会先从缓存中查找，缓存未命中的关键词会请求百度 API。',
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
                        'items': {'type': 'string'},
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
                    'msg': {'type': 'string', 'example': '关键词检查完成'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'results': {
                                'type': 'object',
                                'additionalProperties': {
                                    'type': 'object',
                                    'properties': {
                                        'exists': {'type': 'boolean'}
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
        
        if len(words) == 0:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "关键词列表不能为空"))
        
        # 去重
        words = list(set(words))
        
        log.info(f"开始检查关键词, 数量: {len(words)}")
        
        # 获取 Redis 客户端
        redis_client = get_redis_client()
        
        # Step 1: 从缓存中查找已检查过的关键词
        cached_results = check_words_from_cache(words, redis_client)
        log.info(f"从缓存中找到 {len(cached_results)} 个已检查的关键词")
        
        # 找出未检查过的关键词
        uncached_words = [w for w in words if w not in cached_results]
        
        # 如果所有关键词都在缓存中，直接返回
        if not uncached_words:
            log.info("所有关键词都在缓存中，直接返回结果")
            results = {word: {'exists': r['exists']} for word, r in cached_results.items()}
            return jsonify(ResponseFormatter.success({
                'results': results
            }, "关键词检查完成"))
        
        log.info(f"需要请求百度 API 检查 {len(uncached_words)} 个关键词")
        
        # Step 2: 创建 Scrapy 任务检查未缓存的关键词
        task_name = f'关键词检查-{len(uncached_words)}个词'
        parameters = {
            'keywords': uncached_words,
        }
        
        task_id = task_scheduler.create_task(
            task_type='word_check',
            parameters=parameters,
            task_name=task_name,
            priority=10  # 高优先级
        )
        
        if not task_id:
            return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, "创建检查任务失败"))
        
        log.info(f"创建检查任务成功: {task_id}")
        
        # Step 3: 等待任务结果
        api_results = wait_for_task_results(task_id, uncached_words, redis_client, timeout=30)
        
        # Step 4: 合并缓存结果和 API 结果
        final_results = {}
        
        # 添加缓存结果
        for word, result in cached_results.items():
            final_results[word] = {'exists': result['exists']}
        
        # 添加 API 结果
        for word, result in api_results.items():
            final_results[word] = result
        
        log.info(f"关键词检查完成，共 {len(final_results)} 个结果")
        
        return jsonify(ResponseFormatter.success({
            'results': final_results
        }, "关键词检查完成"))
        
    except Exception as e:
        log.error(f"检查关键词失败: {e}")
        import traceback
        log.error(traceback.format_exc())
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"检查关键词失败: {str(e)}"))


@word_check_blueprint.route('/cache/<keyword>', methods=['GET'])
@swag_from({
    'tags': ['关键词检查'],
    'summary': '查询关键词缓存',
    'description': '查询指定关键词的缓存状态',
    'parameters': [
        {
            'name': 'keyword',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '要查询的关键词'
        }
    ],
    'responses': {
        '200': {
            'description': '查询成功'
        }
    }
})
def get_word_cache(keyword):
    """查询关键词缓存"""
    try:
        redis_client = get_redis_client()
        redis_key = f"{REDIS_KEY_PREFIX}{keyword}"
        cached_data = redis_client.get(redis_key)
        
        if cached_data:
            data = json.loads(cached_data)
            return jsonify(ResponseFormatter.success({
                'keyword': keyword,
                'exists': data.get('exists', False),
                'cached': True,
                'checked_at': data.get('checked_at')
            }, "查询成功"))
        else:
            return jsonify(ResponseFormatter.success({
                'keyword': keyword,
                'cached': False
            }, "关键词未缓存"))
            
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"查询失败: {str(e)}"))


@word_check_blueprint.route('/cache/<keyword>', methods=['DELETE'])
@swag_from({
    'tags': ['关键词检查'],
    'summary': '删除关键词缓存',
    'description': '删除指定关键词的缓存',
    'parameters': [
        {
            'name': 'keyword',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '要删除缓存的关键词'
        }
    ],
    'responses': {
        '200': {
            'description': '删除成功'
        }
    }
})
def delete_word_cache(keyword):
    """删除关键词缓存"""
    try:
        redis_client = get_redis_client()
        redis_key = f"{REDIS_KEY_PREFIX}{keyword}"
        redis_client.delete(redis_key)
        
        return jsonify(ResponseFormatter.success({
            'keyword': keyword,
            'deleted': True
        }, "缓存已删除"))
            
    except Exception as e:
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"删除失败: {str(e)}"))


@word_check_blueprint.route('/task/<task_id>', methods=['GET'])
@swag_from({
    'tags': ['关键词检查'],
    'summary': '获取关键词检查任务状态',
    'description': '获取指定任务ID的关键词检查任务状态和结果',
    'parameters': [
        {
            'name': 'task_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '任务ID'
        }
    ],
    'responses': {
        '200': {
            'description': '获取成功'
        }
    }
})
def get_word_check_task(task_id):
    """获取关键词检查任务状态"""
    try:
        task_info = task_scheduler.get_task(task_id)
        
        if not task_info:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, f"任务不存在: {task_id}"))
        
        return jsonify(ResponseFormatter.success(task_info, "获取任务状态成功"))
        
    except Exception as e:
        log.error(f"获取任务状态失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取任务状态失败: {str(e)}"))


def register_word_check_blueprint(app):
    """注册关键词检查蓝图"""
    app.register_blueprint(word_check_blueprint)