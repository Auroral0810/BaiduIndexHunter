"""
统计API控制器
提供任务统计数据的HTTP接口
"""
from flask import Blueprint, jsonify
from flasgger import swag_from

from src.core.logger import log
from src.core.constants.respond import ResponseCode, ResponseFormatter
from src.services.statistics_service import statistics_service
from src.api.schemas.statistics import (
    TaskSummaryRequest,
    TaskSummaryResponse,
    GetSpiderStatisticsRequest,
    SpiderStatisticsResponse,
    GetKeywordStatisticsRequest,
    KeywordStatisticsResponse,
    GetCityStatisticsRequest,
    CityStatisticsResponse,
    DashboardRequest,
    DashboardDataResponse
)
from src.api.utils.validators import validate_args
from src.api.utils.swagger import create_swagger_spec

# 创建蓝图
stats_blueprint = Blueprint('statistics', __name__, url_prefix='/api/statistics')

# ============== Swagger 规范定义 ==============

TASK_SUMMARY_SPEC = create_swagger_spec(
    request_schema=TaskSummaryRequest,
    response_schema=TaskSummaryResponse,
    summary="获取任务统计摘要",
    description="获取系统中任务的统计摘要数据",
    tags=["统计数据"],
    request_in="query"
)

TASK_STATISTICS_SPEC = create_swagger_spec(
    summary="获取任务统计数据",
    description="获取指定任务的统计数据",
    tags=["统计数据"],
    parameters=[{
        'name': 'task_id',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': '任务ID'
    }]
)

SPIDER_STATISTICS_SPEC = create_swagger_spec(
    request_schema=GetSpiderStatisticsRequest,
    response_schema=SpiderStatisticsResponse,
    summary="获取爬虫统计数据",
    description="获取爬虫执行的统计数据，支持按日期和任务类型筛选",
    tags=["统计数据"],
    request_in="query"
)

KEYWORD_STATISTICS_SPEC = create_swagger_spec(
    request_schema=GetKeywordStatisticsRequest,
    response_schema=KeywordStatisticsResponse,
    summary="获取关键词统计数据",
    description="获取关键词的统计数据",
    tags=["统计数据"],
    request_in="query"
)

CITY_STATISTICS_SPEC = create_swagger_spec(
    request_schema=GetCityStatisticsRequest,
    response_schema=CityStatisticsResponse,
    summary="获取城市统计数据",
    description="获取城市维度的统计数据",
    tags=["统计数据"],
    request_in="query"
)

DASHBOARD_SPEC = create_swagger_spec(
    request_schema=DashboardRequest,
    response_schema=DashboardDataResponse,
    summary="获取大屏展示数据",
    description="获取大屏展示数据，包括任务趋势、成功率、爬取量等",
    tags=["统计数据"],
    request_in="query"
)


# ============== API 端点 ==============

@stats_blueprint.route('/task_summary', methods=['GET'])
@swag_from(TASK_SUMMARY_SPEC)
@validate_args(TaskSummaryRequest)
def get_task_summary(validated_data: TaskSummaryRequest):
    """获取任务统计摘要"""
    try:
        data = statistics_service.get_task_summary(validated_data.days)
        return jsonify(ResponseFormatter.success(data, "获取任务统计摘要成功"))
    except Exception as e:
        log.error(f"获取任务统计摘要失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取任务统计摘要失败: {str(e)}"))


@stats_blueprint.route('/task_statistics/<task_id>', methods=['GET'])
@swag_from(TASK_STATISTICS_SPEC)
def get_task_statistics(task_id):
    """获取任务统计数据"""
    try:
        data = statistics_service.get_task_statistics(task_id)
        if not data:
             # Ideally service should handle not found or return empty list.
             # If empty list is valid response for valid task but no stats, then success.
             # If task itself doesn't exist, we might want to check that first.
             # Current implementation in Service just queries stats.
             # Let's keep it simple.
             pass
        return jsonify(ResponseFormatter.success(data, "获取任务统计数据成功"))
    except Exception as e:
        log.error(f"获取任务统计数据失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取任务统计数据失败: {str(e)}"))


@stats_blueprint.route('/spider_statistics', methods=['GET'])
@swag_from(SPIDER_STATISTICS_SPEC)
@validate_args(GetSpiderStatisticsRequest)
def get_spider_statistics(validated_data: GetSpiderStatisticsRequest):
    """获取爬虫统计数据"""
    try:
        data = statistics_service.get_spider_statistics(validated_data.date, validated_data.task_type)
        return jsonify(ResponseFormatter.success({'statistics': data}, "获取爬虫统计数据成功"))
    except Exception as e:
        log.error(f"获取爬虫统计数据失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取爬虫统计数据失败: {str(e)}"))


@stats_blueprint.route('/keyword_statistics', methods=['GET'])
@swag_from(KEYWORD_STATISTICS_SPEC)
@validate_args(GetKeywordStatisticsRequest)
def get_keyword_statistics(validated_data: GetKeywordStatisticsRequest):
    """获取关键词统计数据"""
    try:
        data = statistics_service.get_keyword_statistics(validated_data.task_id, validated_data.limit)
        return jsonify(ResponseFormatter.success(data, "获取关键词统计数据成功"))
    except Exception as e:
        log.error(f"获取关键词统计数据失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取关键词统计数据失败: {str(e)}"))


@stats_blueprint.route('/city_statistics', methods=['GET'])
@swag_from(CITY_STATISTICS_SPEC)
@validate_args(GetCityStatisticsRequest)
def get_city_statistics(validated_data: GetCityStatisticsRequest):
    """获取城市统计数据"""
    try:
        data = statistics_service.get_city_statistics(validated_data.city_name, validated_data.task_type, validated_data.limit)
        return jsonify(ResponseFormatter.success(data, "获取城市统计数据成功"))
    except Exception as e:
        log.error(f"获取城市统计数据失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取城市统计数据失败: {str(e)}"))


@stats_blueprint.route('/dashboard', methods=['GET'])
@swag_from(DASHBOARD_SPEC)
@validate_args(DashboardRequest)
def get_dashboard_data(validated_data: DashboardRequest):
    """获取大屏展示数据"""
    try:
        data = statistics_service.get_dashboard_data(
            validated_data.days,
            validated_data.start_date,
            validated_data.end_date
        )
        return jsonify(ResponseFormatter.success(data, "获取大屏数据成功"))
    except Exception as e:
        log.error(f"获取大屏数据失败: {e}")
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, f"获取大屏数据失败: {str(e)}"))


def register_statistics_blueprint(app):
    """注册统计蓝图"""
    app.register_blueprint(stats_blueprint)