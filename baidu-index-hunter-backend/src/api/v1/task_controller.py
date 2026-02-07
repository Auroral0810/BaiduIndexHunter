"""
任务控制器API
提供任务管理的HTTP接口
"""
import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from flasgger import swag_from

from src.core.logger import log
from src.core.constants.respond import ResponseCode, ResponseFormatter
from src.api.schemas.task import (
    CreateTaskRequest,
    ListTasksRequest,
    TaskListResponse,
    TaskDetailResponse,
    TaskCreateResponse,
    DownloadFileRequest
)
from src.api.utils.validators import validate_args, validate_json
from src.api.utils.swagger import create_swagger_spec
from src.services.task_service import task_service
from src.scheduler.scheduler import task_scheduler  # 用于启动调度器
from src.core.auth import auth_before_request

# 创建蓝图
task_blueprint = Blueprint('task', __name__, url_prefix='/api/task')
task_blueprint.before_request(auth_before_request)


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
@validate_json(CreateTaskRequest)
def create_task(validated_data: CreateTaskRequest):
    """创建爬虫任务"""
    try:
        # 参数已由 @validate_json 校验并注入为 CreateTaskRequest 对象
        task_type = validated_data.taskType.value 
        parameters = validated_data.parameters
        priority = validated_data.priority
        
        # 调用 Service 创建任务
        try:
            task_id = task_service.create_task(task_type, parameters, priority)
            return jsonify(ResponseFormatter.success({
                'taskId': task_id
            }, "任务创建成功"))
        except ValueError as e:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, str(e)))
            
    except Exception as e:
        log.error(f"创建任务失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"创建任务失败: {str(e)}"))


@task_blueprint.route('/list', methods=['GET'])
@swag_from(LIST_TASKS_SPEC)
@validate_args(ListTasksRequest)
def list_tasks(validated_data: ListTasksRequest):
    """获取任务列表"""
    try:
        # 获取任务列表
        tasks = task_service.list_tasks(
            status=validated_data.status,
            task_type=validated_data.task_type,
            created_by=validated_data.created_by,
            limit=validated_data.limit,
            offset=validated_data.offset
        )
        
        # 获取总数
        total = task_service.count_tasks(
            status=validated_data.status,
            task_type=validated_data.task_type,
            created_by=validated_data.created_by
        )
        
        # 处理日期时间格式
        for task in tasks:
            for key, value in task.items():
                if isinstance(value, datetime):
                    task[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            
            # 简单的参数JSON解析 (为了View层展示)
            for json_field in ['parameters', 'output_files', 'checkpoint_path']:
                if json_field in task and task[json_field]:
                    try:
                        if isinstance(task[json_field], str):
                             task[json_field] = json.loads(task[json_field])
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
        task = task_service.get_task(task_id)
        
        if not task:
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "任务不存在"))
        
        for key, value in task.items():
            if isinstance(value, datetime):
                task[key] = value.strftime('%Y-%m-%d %H:%M:%S')
        
        for json_field in ['parameters', 'output_files', 'checkpoint_path']:
            if json_field in task and task[json_field]:
                try:
                    if isinstance(task[json_field], str):
                         task[json_field] = json.loads(task[json_field])
                except Exception:
                    pass

        logs = task_service.get_task_logs(task_id, limit=100)
        for lg in logs:
            if 'timestamp' in lg and isinstance(lg['timestamp'], datetime):
                lg['timestamp'] = lg['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
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
        result = task_service.start_task(task_id)
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
        result = task_service.pause_task(task_id)
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
        result = task_service.resume_task(task_id)
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
        result = task_scheduler.cancel_task(task_id) # 直接调用 Scheduler
        
        if result:
            return jsonify(ResponseFormatter.success(None, "任务取消成功"))
        else:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "任务取消失败"))
    except Exception as e:
        log.error(f"取消任务失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"取消任务失败: {str(e)}"))


@task_blueprint.route('/download', methods=['GET'])
@swag_from(DOWNLOAD_FILE_SPEC)
# @validate_args(DownloadFileRequest) # File download params usually in query, can add this later if strict validation needed
def download_file():
    """下载文件"""
    try:
        file_path = request.args.get('filePath')
        if not file_path:
            return jsonify(ResponseFormatter.error(ResponseCode.PARAM_ERROR, "缺少必要参数: filePath"))
        
        if not os.path.isfile(file_path):
            return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "文件不存在"))
        
        file_name = os.path.basename(file_path)
        
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