"""
任务控制器API
提供任务管理的HTTP接口
"""

import json
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from flasgger import swag_from

from src.core.logger import log
from src.core.constants.respond import ResponseCode, ResponseFormatter
from src.scheduler.scheduler import task_scheduler
from src.api.schemas.task import (
    CreateTaskRequest,
    ListTasksRequest,
    TaskListResponse,
    TaskDetailResponse,
    TaskCreateResponse,
    DownloadFileRequest
)
from src.api.utils.validators import validate_args
from src.api.utils.swagger import create_swagger_spec

# 创建蓝图
task_blueprint = Blueprint('task', __name__, url_prefix='/api/task')


# ============== Swagger 规范定义 ==============

LIST_TASKS_SPEC = create_swagger_spec(
    request_schema=ListTasksRequest,
    response_schema=TaskListResponse,
    summary="获取任务列表",
    description="获取任务列表，支持分页和筛选",
    tags=["任务管理"],
    request_in="query"
)

GET_TASK_SPEC = create_swagger_spec(
    response_schema=TaskDetailResponse,
    summary="获取任务详情",
    description="根据任务ID获取任务详情",
    tags=["任务管理"],
    parameters=[{
        'name': 'task_id',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': '任务ID'
    }]
)

TASK_ACTION_SPEC = lambda action: create_swagger_spec(
    summary=f"{action}任务",
    description=f"{action}指定的任务",
    tags=["任务管理"],
    parameters=[{
        'name': 'task_id',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': '任务ID'
    }]
)

DOWNLOAD_FILE_SPEC = create_swagger_spec(
    summary="下载任务结果文件",
    description="下载指定路径的任务结果文件",
    tags=["任务管理"],
    parameters=[{
        'name': 'filePath',
        'in': 'query',
        'type': 'string',
        'required': True,
        'description': '文件路径'
    }]
)

CREATE_TASK_SPEC = create_swagger_spec(
    request_schema=CreateTaskRequest,
    response_schema=TaskCreateResponse,
    summary="创建爬虫任务",
    description="创建一个新的爬虫任务",
    tags=["任务管理"],
    request_in="body"
)

@task_blueprint.route('/create', methods=['POST'])
@swag_from(CREATE_TASK_SPEC)
def create_task():
    """创建爬虫任务"""
    try:
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "请求参数为空"))
        
        # 验证必要参数
        task_type = data.get('taskType')
        parameters = data.get('parameters')
        
        if not task_type or not parameters:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: taskType 或 parameters"))
        
        # 验证任务类型
        valid_task_types = ['search_index', 'feed_index', 'word_graph', 
                          'demographic_attributes', 'interest_profile', 'region_distribution']
        if task_type not in valid_task_types:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, f"无效的任务类型: {task_type}"))
        
        # 获取可选参数
        priority = data.get('priority', 5)  # 默认优先级为5
        
        # 处理搜索指数任务
        if task_type == 'search_index':
            # 验证搜索指数任务的参数
            if 'keywords' not in parameters or not parameters['keywords']:
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: keywords"))
            
            # 验证城市参数
            if 'cities' not in parameters or not parameters['cities']:
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: cities"))
            
            # 处理时间参数
            time_params_count = sum(1 for param in ['days', 'date_ranges', 'year_range'] if param in parameters)
            
            # 处理恢复任务
            resume = parameters.get('resume', False)
            if resume and ('task_id' not in parameters or not parameters['task_id']):
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "恢复任务时必须提供task_id"))
            
            # 准备爬虫参数
            spider_params = {
                'keywords': parameters['keywords'],
                'cities': parameters['cities'],
                'resume': resume
            }
            
            # 添加 kind 参数（数据来源：PC/移动/PC+移动）
            if 'kind' in parameters:
                spider_params['kind'] = parameters['kind']
            
            # 添加时间相关参数
            if 'days' in parameters:
                spider_params['days'] = parameters['days']
            elif 'date_ranges' in parameters:
                spider_params['date_ranges'] = parameters['date_ranges']
            elif 'year_range' in parameters and parameters['year_range']:
                # 处理年份参数，支持多种格式
                try:
                    year_range = parameters['year_range']
                    
                    if isinstance(year_range, list) and len(year_range) > 0:
                        # 检查第一个元素的类型来判断格式
                        first_element = year_range[0]
                        
                        if isinstance(first_element, list):
                            # 格式1: 嵌套格式 [[start, end]]
                            spider_params['year_range'] = year_range
                        elif len(year_range) == 2:
                            # 格式2: 两个元素的列表 [2006, 2026] 或 ["2006", "2026"]，转换为嵌套格式 [[2006, 2026]]
                            start_year = int(year_range[0])
                            end_year = int(year_range[1])
                            spider_params['year_range'] = [[start_year, end_year]]
                        elif len(year_range) > 2:
                            # 格式3: 多个年份列表 ["2006", "2007", "2008", ...]
                            # 将每个年份转换为独立的范围
                            year_ranges = []
                            for year_str in year_range:
                                year = int(year_str)
                                year_ranges.append([year, year])
                            spider_params['year_range'] = year_ranges
                        else:
                            raise ValueError("year_range 格式错误：列表长度不足")
                    else:
                        raise ValueError("year_range 格式错误：不是有效的列表")
                    
                except (ValueError, TypeError, IndexError) as e:
                    return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, f"无效的年份范围: {str(e)}"))
            
            # 添加任务ID（如果是恢复任务）
            if resume and 'task_id' in parameters:
                spider_params['task_id'] = parameters['task_id']
            
            # 调试日志：打印转换后的爬虫参数
            log.info(f"搜索指数任务 - 转换后的 year_range: {spider_params.get('year_range')}")
            
            # 创建任务
            task_id = task_scheduler.create_task(
                task_type=task_type,
                parameters=spider_params,
                task_name=f"搜索指数_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                created_by=None,
                priority=priority
            )
            
            # 如果是恢复任务，设置断点续传数据
            if resume and 'task_id' in parameters:
                # 获取原任务的断点续传数据
                original_task = task_scheduler.get_task(parameters['task_id'])
                if original_task and 'checkpoint_path' in original_task and original_task['checkpoint_path']:
                    # 更新新任务的断点续传数据
                    task_scheduler.update_task_checkpoint(task_id, original_task['checkpoint_path'])
            
            # 启动任务
            task_scheduler.start_task(task_id)
            
            return jsonify(ResponseFormatter.success({
                'taskId': task_id
            }, "搜索指数任务创建成功"))
            
        # 处理资讯指数任务
        elif task_type == 'feed_index':
            # 验证资讯指数任务的参数
            if 'keywords' not in parameters or not parameters['keywords']:
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: keywords"))
            
            # 验证城市参数
            if 'cities' not in parameters or not parameters['cities']:
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: cities"))
            
            # 处理时间参数
            time_params_count = sum(1 for param in ['days', 'date_ranges', 'year_range'] if param in parameters)
            
            # 处理恢复任务
            resume = parameters.get('resume', False)
            if resume and ('task_id' not in parameters or not parameters['task_id']):
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "恢复任务时必须提供task_id"))
            
            # 准备爬虫参数
            spider_params = {
                'keywords': parameters['keywords'],
                'cities': parameters['cities'],
                'resume': resume
            }
            
            # 添加 kind 参数（数据来源：PC/移动/PC+移动）
            if 'kind' in parameters:
                spider_params['kind'] = parameters['kind']
            
            # 添加时间相关参数
            if 'days' in parameters:
                spider_params['days'] = parameters['days']
            elif 'date_ranges' in parameters:
                spider_params['date_ranges'] = parameters['date_ranges']
            elif 'year_range' in parameters and parameters['year_range']:
                # 处理年份参数，支持多种格式
                try:
                    year_range = parameters['year_range']
                    
                    if isinstance(year_range, list) and len(year_range) > 0:
                        # 检查第一个元素的类型来判断格式
                        first_element = year_range[0]
                        
                        if isinstance(first_element, list):
                            # 格式1: 嵌套格式 [[start, end]]
                            spider_params['year_range'] = year_range
                        elif len(year_range) == 2:
                            # 格式2: 两个元素的列表 [2006, 2026] 或 ["2006", "2026"]，转换为嵌套格式 [[2006, 2026]]
                            start_year = int(year_range[0])
                            end_year = int(year_range[1])
                            spider_params['year_range'] = [[start_year, end_year]]
                        elif len(year_range) > 2:
                            # 格式3: 多个年份列表 ["2006", "2007", "2008", ...]
                            # 将每个年份转换为独立的范围
                            year_ranges = []
                            for year_str in year_range:
                                year = int(year_str)
                                year_ranges.append([year, year])
                            spider_params['year_range'] = year_ranges
                        else:
                            raise ValueError("year_range 格式错误：列表长度不足")
                    else:
                        raise ValueError("year_range 格式错误：不是有效的列表")
                    
                except (ValueError, TypeError, IndexError) as e:
                    return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, f"无效的年份范围: {str(e)}"))
            
            # 添加任务ID（如果是恢复任务）
            if resume and 'task_id' in parameters:
                spider_params['task_id'] = parameters['task_id']
            
            # 创建任务
            task_id = task_scheduler.create_task(
                task_type=task_type,
                parameters=spider_params,
                task_name=f"资讯指数_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                created_by=None,
                priority=priority
            )
            
            # 如果是恢复任务，设置断点续传数据
            if resume and 'task_id' in parameters:
                # 获取原任务的断点续传数据
                original_task = task_scheduler.get_task(parameters['task_id'])
                if original_task and 'checkpoint_path' in original_task and original_task['checkpoint_path']:
                    # 更新新任务的断点续传数据
                    task_scheduler.update_task_checkpoint(task_id, original_task['checkpoint_path'])
            
            # 启动任务
            task_scheduler.start_task(task_id)
            
            return jsonify(ResponseFormatter.success({
                'taskId': task_id
            }, "资讯指数任务创建成功"))
        
        # 处理需求图谱任务
        elif task_type == 'word_graph':
            # 验证需求图谱任务的参数
            if 'keywords' not in parameters or not parameters['keywords']:
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: keywords"))
            
            if 'datelists' not in parameters or not parameters['datelists']:
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: datelists"))
            
            # 处理恢复任务
            resume = parameters.get('resume', False)
            if resume and ('task_id' not in parameters or not parameters['task_id']):
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "恢复任务时必须提供task_id"))
            
            # 获取输出格式
            output_format = parameters.get('output_format', 'csv')
            if output_format not in ['csv', 'excel']:
                output_format = 'csv'
            
            # 准备爬虫参数
            spider_params = {
                'keywords': parameters['keywords'],
                'datelists': parameters['datelists'],
                'output_format': output_format,
                'resume': resume
            }
            
            # 添加 kind 参数（数据来源：PC/移动/PC+移动）
            if 'kind' in parameters:
                spider_params['kind'] = parameters['kind']
            
            # 添加任务ID（如果是恢复任务）
            if resume and 'task_id' in parameters:
                spider_params['task_id'] = parameters['task_id']
            
            # 创建任务
            task_id = task_scheduler.create_task(
                task_type=task_type,
                parameters=spider_params,
                task_name=f"需求图谱_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                created_by=None,
                priority=priority
            )
            
            # 如果是恢复任务，设置断点续传数据
            if resume and 'task_id' in parameters:
                # 获取原任务的断点续传数据
                original_task = task_scheduler.get_task(parameters['task_id'])
                if original_task and 'checkpoint_path' in original_task and original_task['checkpoint_path']:
                    # 更新新任务的断点续传数据
                    task_scheduler.update_task_checkpoint(task_id, original_task['checkpoint_path'])
            
            # 启动任务
            task_scheduler.start_task(task_id)
            
            return jsonify(ResponseFormatter.success({
                'taskId': task_id
            }, "需求图谱任务创建成功"))
        
        # 处理人群属性任务
        elif task_type == 'demographic_attributes':
            # 验证人群属性任务的参数
            if 'keywords' not in parameters or not parameters['keywords']:
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: keywords"))
            
            # 处理恢复任务
            resume = parameters.get('resume', False)
            if resume and ('task_id' not in parameters or not parameters['task_id']):
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "恢复任务时必须提供task_id"))
            
            # 获取输出格式
            output_format = parameters.get('output_format', 'csv')
            if output_format not in ['csv', 'excel']:
                output_format = 'csv'
            
            # 获取批处理大小
            batch_size = parameters.get('batch_size', 10)
            if not isinstance(batch_size, int) or batch_size <= 0:
                batch_size = 10
            
            # 准备爬虫参数
            spider_params = {
                'keywords': parameters['keywords'],
                'output_format': output_format,
                'batch_size': batch_size,
                'resume': resume
            }
            
            # 添加 kind 参数（数据来源：PC/移动/PC+移动）
            if 'kind' in parameters:
                spider_params['kind'] = parameters['kind']
            
            # 添加任务ID（如果是恢复任务）
            if resume and 'task_id' in parameters:
                spider_params['task_id'] = parameters['task_id']
            
            # 创建任务
            task_id = task_scheduler.create_task(
                task_type=task_type,
                parameters=spider_params,
                task_name=f"人群属性_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                created_by=None,
                priority=priority
            )
            
            # 如果是恢复任务，设置断点续传数据
            if resume and 'task_id' in parameters:
                # 获取原任务的断点续传数据
                original_task = task_scheduler.get_task(parameters['task_id'])
                if original_task and 'checkpoint_path' in original_task and original_task['checkpoint_path']:
                    # 更新新任务的断点续传数据
                    task_scheduler.update_task_checkpoint(task_id, original_task['checkpoint_path'])
            
            # 启动任务
            task_scheduler.start_task(task_id)
            
            return jsonify(ResponseFormatter.success({
                'taskId': task_id
            }, "人群属性任务创建成功"))
        
        # 处理兴趣分布任务
        elif task_type == 'interest_profile':
            # 验证兴趣分布任务的参数
            if 'keywords' not in parameters or not parameters['keywords']:
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: keywords"))
            
            # 处理恢复任务
            resume = parameters.get('resume', False)
            if resume and ('task_id' not in parameters or not parameters['task_id']):
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "恢复任务时必须提供task_id"))
            
            # 获取输出格式
            output_format = parameters.get('output_format', 'csv')
            if output_format not in ['csv', 'excel']:
                output_format = 'csv'
            
            # 获取批处理大小
            batch_size = parameters.get('batch_size', 10)
            if not isinstance(batch_size, int) or batch_size <= 0:
                batch_size = 10
            
            # 准备爬虫参数
            spider_params = {
                'keywords': parameters['keywords'],
                'output_format': output_format,
                'batch_size': batch_size,
                'resume': resume
            }
            
            # 添加 kind 参数（数据来源：PC/移动/PC+移动）
            if 'kind' in parameters:
                spider_params['kind'] = parameters['kind']
            
            # 添加任务ID（如果是恢复任务）
            if resume and 'task_id' in parameters:
                spider_params['task_id'] = parameters['task_id']
            
            # 创建任务
            task_id = task_scheduler.create_task(
                task_type=task_type,
                parameters=spider_params,
                task_name=f"兴趣分布_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                created_by=None,
                priority=priority
            )
            
            # 如果是恢复任务，设置断点续传数据
            if resume and 'task_id' in parameters:
                # 获取原任务的断点续传数据
                original_task = task_scheduler.get_task(parameters['task_id'])
                if original_task and 'checkpoint_path' in original_task and original_task['checkpoint_path']:
                    # 更新新任务的断点续传数据
                    task_scheduler.update_task_checkpoint(task_id, original_task['checkpoint_path'])
            
            # 启动任务
            task_scheduler.start_task(task_id)
            
            return jsonify(ResponseFormatter.success({
                'taskId': task_id
            }, "兴趣分布任务创建成功"))
        
        # 处理地域分布任务
        elif task_type == 'region_distribution':
            # 验证地域分布任务的参数
            if 'keywords' not in parameters or not parameters['keywords']:
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: keywords"))
            
            if 'regions' not in parameters or not parameters['regions']:
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: regions"))
            
            # 处理时间参数
            time_params_count = sum(1 for param in ['days', 'date_ranges', 'year_range', 'start_date', 'end_date'] if param in parameters)
            
            # 处理恢复任务
            resume = parameters.get('resume', False)
            if resume and ('task_id' not in parameters or not parameters['task_id']):
                return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "恢复任务时必须提供task_id"))
            
            # 获取输出格式
            output_format = parameters.get('output_format', 'csv')
            if output_format not in ['csv', 'excel']:
                output_format = 'csv'
            
            # 准备爬虫参数
            spider_params = {
                'keywords': parameters['keywords'],
                'regions': parameters['regions'],
                'output_format': output_format,
                'resume': resume
            }
            
            # 添加 kind 参数（数据来源：PC/移动/PC+移动）
            if 'kind' in parameters:
                spider_params['kind'] = parameters['kind']
            
            # 添加时间相关参数
            if 'days' in parameters:
                spider_params['days'] = parameters['days']
            elif 'date_ranges' in parameters:
                spider_params['date_ranges'] = parameters['date_ranges']
            elif 'yearRange' in parameters and parameters['yearRange']:
                # 处理年份参数（驼峰格式）
                try:
                    year_range = parameters['yearRange']
                    log.info(f"识别到 yearRange (驼峰格式): {year_range}")
                    
                    if isinstance(year_range, list) and len(year_range) > 0:
                        # 检查第一个元素的类型来判断格式
                        first_element = year_range[0]
                        
                        if isinstance(first_element, list):
                            # 格式1: 嵌套格式 [[start, end]]
                            spider_params['year_range'] = year_range
                        elif len(year_range) == 2:
                            # 格式2: 两个元素的列表 [2006, 2026] 或 ["2006", "2026"]，转换为嵌套格式 [[2006, 2026]]
                            start_year = int(year_range[0])
                            end_year = int(year_range[1])
                            spider_params['year_range'] = [[start_year, end_year]]
                        elif len(year_range) > 2:
                            # 格式3: 多个年份列表 ["2006", "2007", "2008", ...]
                            # 将每个年份转换为独立的范围
                            year_ranges = []
                            for year_str in year_range:
                                year = int(year_str)
                                year_ranges.append([year, year])
                            spider_params['year_range'] = year_ranges
                        else:
                            raise ValueError("yearRange 格式错误：列表长度不足")
                    else:
                        raise ValueError("yearRange 格式错误：不是有效的列表")
                    
                except (ValueError, TypeError, IndexError) as e:
                    return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, f"无效的年份范围: {str(e)}"))
            elif 'year_range' in parameters and parameters['year_range']:
                # 处理年份参数（下划线格式）
                try:
                    year_range = parameters['year_range']
                    log.info(f"识别到 year_range (下划线格式): {year_range}")
                    
                    if isinstance(year_range, list) and len(year_range) > 0:
                        # 检查第一个元素的类型来判断格式
                        first_element = year_range[0]
                        
                        if isinstance(first_element, list):
                            # 格式1: 嵌套格式 [[start, end]]
                            spider_params['year_range'] = year_range
                        elif len(year_range) == 2:
                            # 格式2: 两个元素的列表 [2006, 2026] 或 ["2006", "2026"]，转换为嵌套格式 [[2006, 2026]]
                            start_year = int(year_range[0])
                            end_year = int(year_range[1])
                            spider_params['year_range'] = [[start_year, end_year]]
                        elif len(year_range) > 2:
                            # 格式3: 多个年份列表 ["2006", "2007", "2008", ...]
                            # 将每个年份转换为独立的范围
                            year_ranges = []
                            for year_str in year_range:
                                year = int(year_str)
                                year_ranges.append([year, year])
                            spider_params['year_range'] = year_ranges
                        else:
                            raise ValueError("year_range 格式错误：列表长度不足")
                    else:
                        raise ValueError("year_range 格式错误：不是有效的列表")
                    
                except (ValueError, TypeError, IndexError) as e:
                    return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, f"无效的年份范围: {str(e)}"))
            elif 'start_date' in parameters and 'end_date' in parameters:
                spider_params['start_date'] = parameters['start_date']
                spider_params['end_date'] = parameters['end_date']
            
            # 添加区域级别参数
            if 'regionLevel' in parameters:
                spider_params['region_level'] = parameters['regionLevel']
            
            # 添加任务ID（如果是恢复任务）
            if resume and 'task_id' in parameters:
                spider_params['task_id'] = parameters['task_id']
            
            # 创建任务
            task_id = task_scheduler.create_task(
                task_type=task_type,
                parameters=spider_params,
                task_name=f"地域分布_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                created_by=None,
                priority=priority
            )
            
            # 如果是恢复任务，设置断点续传数据
            if resume and 'task_id' in parameters:
                # 获取原任务的断点续传数据
                original_task = task_scheduler.get_task(parameters['task_id'])
                if original_task and 'checkpoint_path' in original_task and original_task['checkpoint_path']:
                    # 更新新任务的断点续传数据
                    task_scheduler.update_task_checkpoint(task_id, original_task['checkpoint_path'])
            
            # 启动任务
            task_scheduler.start_task(task_id)
            
            return jsonify(ResponseFormatter.success({
                'taskId': task_id
            }, "地域分布任务创建成功"))
        
        # 其他类型任务的处理...
        
        # 默认创建任务
        task_id = task_scheduler.create_task(
            task_type=task_type,
            parameters=parameters,
            task_name=f"{task_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            created_by=None,
            priority=priority
        )
        
        return jsonify(ResponseFormatter.success({
            'taskId': task_id
        }, "任务创建成功"))
        
    except Exception as e:
        log.error(f"创建任务失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"创建任务失败: {str(e)}"))


@task_blueprint.route('/list', methods=['GET'])
@swag_from(LIST_TASKS_SPEC)
@validate_args(ListTasksRequest)
def list_tasks(validated_data: ListTasksRequest):
    """获取任务列表"""
    try:
        # 从校验后的数据获取参数
        status = validated_data.status
        task_type = validated_data.task_type
        created_by = validated_data.created_by
        keyword = validated_data.keyword
        limit = validated_data.limit
        offset = validated_data.offset
        
        # 获取任务列表
        tasks = task_scheduler.list_tasks(
            status=status,
            task_type=task_type,
            created_by=created_by,
            limit=limit,
            offset=offset
        )
        
        # 获取总数
        total = task_scheduler.count_tasks(
            status=status,
            task_type=task_type,
            created_by=created_by
        )
        
        # 处理日期时间格式
        for task in tasks:
            for key, value in task.items():
                if isinstance(value, datetime):
                    task[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            # 处理JSON字段
            if 'parameters' in task and task['parameters']:
                try:
                    if isinstance(task['parameters'], str):
                        try:
                            task['parameters'] = json.loads(task['parameters'])
                            if isinstance(task['parameters'], str):
                                task['parameters'] = json.loads(task['parameters'])
                        except Exception:
                            pass
                except Exception:
                    pass
        
        return jsonify(ResponseFormatter.success({
            'total': total,
            'tasks': tasks
        }, "获取任务列表成功"))
        
    except Exception as e:
        log.error(f"获取任务列表失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取任务列表失败: {str(e)}"))



@task_blueprint.route('/<task_id>', methods=['GET'])
@swag_from(GET_TASK_SPEC)
def get_task(task_id):
    """获取任务详情"""
    try:
        # 获取任务详情
        task = task_scheduler.get_task(task_id)
        
        if not task:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "任务不存在"))
        
        # 处理日期时间格式
        for key, value in task.items():
            if isinstance(value, datetime):
                task[key] = value.strftime('%Y-%m-%d %H:%M:%S')
        
        # 获取任务日志
        logs = task_scheduler.get_task_logs(task_id, limit=100)
        
        # 处理日志中的日期时间格式
        for log in logs:
            if 'timestamp' in log and isinstance(log['timestamp'], datetime):
                log['timestamp'] = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        # 将日志添加到任务详情中
        task['logs'] = logs
        
        return jsonify(ResponseFormatter.success(task, "获取任务详情成功"))
        
    except Exception as e:
        log.error(f"获取任务详情失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取任务详情失败: {str(e)}"))


@task_blueprint.route('/<task_id>/start', methods=['POST'])
@swag_from(TASK_ACTION_SPEC('启动'))
def start_task(task_id):
    """启动任务"""
    try:
        # 检查任务是否存在
        task = task_scheduler.get_task(task_id)
        if not task:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "任务不存在"))
        
        # 启动任务
        result = task_scheduler.start_task(task_id)
        
        if result:
            return jsonify(ResponseFormatter.success(None, "任务启动成功"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.BAD_REQUEST, "任务启动失败"))
        
    except Exception as e:
        log.error(f"启动任务失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"启动任务失败: {str(e)}"))


@task_blueprint.route('/<task_id>/pause', methods=['POST'])
@swag_from(TASK_ACTION_SPEC('暂停'))
def pause_task(task_id):
    """暂停任务"""
    try:
        # 检查任务是否存在
        task = task_scheduler.get_task(task_id)
        if not task:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "任务不存在"))
        
        # 暂停任务
        result = task_scheduler.pause_task(task_id)
        
        if result:
            return jsonify(ResponseFormatter.success(None, "任务暂停成功"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "任务暂停失败"))
        
    except Exception as e:
        log.error(f"暂停任务失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"暂停任务失败: {str(e)}"))


@task_blueprint.route('/<task_id>/resume', methods=['POST'])
@swag_from(TASK_ACTION_SPEC('恢复'))
def resume_task(task_id):
    """恢复任务"""
    try:
        # 检查任务是否存在
        task = task_scheduler.get_task(task_id)
        if not task:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "任务不存在"))
        
        # 恢复任务
        result = task_scheduler.resume_task(task_id)
        
        if result:
            return jsonify(ResponseFormatter.success(None, "任务恢复成功"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.BAD_REQUEST, "任务恢复失败"))
        
    except Exception as e:
        log.error(f"恢复任务失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"恢复任务失败: {str(e)}"))


@task_blueprint.route('/<task_id>/cancel', methods=['POST'])
@swag_from(TASK_ACTION_SPEC('取消'))
def cancel_task(task_id):
    """取消任务"""
    try:
        # 检查任务是否存在
        task = task_scheduler.get_task(task_id)
        if not task:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "任务不存在"))
        
        # 取消任务
        result = task_scheduler.cancel_task(task_id)
        
        if result:
            return jsonify(ResponseFormatter.success(None, "任务取消成功"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "任务取消失败"))
        
    except Exception as e:
        log.error(f"取消任务失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"取消任务失败: {str(e)}"))


@task_blueprint.route('/download', methods=['GET'])
@swag_from(DOWNLOAD_FILE_SPEC)
def download_file():
    """下载文件"""
    try:
        # 获取文件路径
        file_path = request.args.get('filePath')
        if not file_path:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: filePath"))
        
        # 检查文件是否存在
        if not os.path.isfile(file_path):
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "文件不存在"))
        
        # 提取文件名
        file_name = os.path.basename(file_path)
        
        # 发送文件
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_name,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        log.error(f"下载文件失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"下载文件失败: {str(e)}"))


def register_task_blueprint(app):
    """注册任务蓝图"""
    app.register_blueprint(task_blueprint)
    
    # 启动任务调度器
    task_scheduler.start()