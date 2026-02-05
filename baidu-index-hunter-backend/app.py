"""
百度指数爬虫API服务 - 应用入口
"""
import os
import sys
from datetime import datetime

from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger

# 核心配置与工具导入 (必须置顶以确保日志格式统一)
from src.core.logger import log, setup_unified_logger, setup_flask_request_logging
from src.core.constants.respond import ResponseCode, ResponseFormatter

# 业务初始化与后台任务服务
from src.services.app_init_service import init_app_data
from src.services.background_task_service import (
    start_background_scheduler, 
    check_cookie_status, 
    update_ab_sr_cookies, 
    resume_paused_tasks
)

# API 蓝图注册器
from src.api.v1.cookie_controller import register_cookie_blueprint
from src.api.v1.region_controller import register_region_blueprint
from src.api.v1.task_controller import register_task_blueprint
from src.api.v1.statistics_controller import register_statistics_blueprint
from src.api.v1.config_api import config_bp
from src.api.v1.word_check_controller import register_word_check_blueprint

# WebSocket 服务
from src.services.websocket_service import init_socketio

# 将项目根目录添加到 Python 路径 (兼容性支持)
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def create_app():
    """创建并配置 Flask 应用"""
    # 1. 基础设置与日志初始化
    unified_log = setup_unified_logger()
    app = Flask(__name__)
    setup_flask_request_logging(app, unified_log)
    
    # 2. 安全与文档配置 (CORS, Swagger)
    CORS(app, supports_credentials=True)
    setup_swagger(app)

    # 3. 业务数据初始化 (全局只执行一次)
    init_app_data()

    # 4. 注册 API 业务蓝图
    register_blueprints(app)

    # 5. 系统组件初始化 (WebSocket, Background Tasks)
    init_socketio(app)
    start_background_scheduler()

    # 6. 注册核心基础路由与错误处理
    register_base_routes(app)
    register_error_handlers(app)

    return app

def setup_swagger(app):
    """配置 Swagger 文档"""
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs/"
    }
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "百度指数爬虫API",
            "description": "百度指数爬虫后端API接口文档",
            "version": "2.0.0",
            "contact": {"name": "API 支持", "email": "15968588744@163.com"}
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey", "name": "Authorization", "in": "header", 
                "description": "JWT Token 认证，格式: Bearer {token}"
            }
        },
        "security": [{"Bearer": []}]
    }
    Swagger(app, config=swagger_config, template=swagger_template)

def register_blueprints(app):
    """注册所有 API 蓝图"""
    register_cookie_blueprint(app)
    register_region_blueprint(app)
    register_task_blueprint(app)
    register_statistics_blueprint(app)
    register_word_check_blueprint(app)
    app.register_blueprint(config_bp)

def register_base_routes(app):
    """注册基础系统路由"""
    @app.route('/')
    def index():
        return jsonify(ResponseFormatter.success({
            "name": "百度指数爬虫API",
            "version": "1.0.0",
            "docs": "/api/docs/"
        }, "欢迎使用百度指数爬虫API"))

    @app.route('/api/health')
    def health_check():
        return jsonify(ResponseFormatter.success({
            "status": "UP",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, "API服务正常"))

    # 管理专用路由 (快捷触发定时任务)
    @app.route('/api/cookie/check')
    def trigger_cookie_check():
        check_cookie_status()
        return jsonify(ResponseFormatter.success(None, "Cookie状态检查已异步触发"))

    @app.route('/api/cookie/update-ab-sr')
    def trigger_ab_sr_update():
        update_ab_sr_cookies()
        return jsonify(ResponseFormatter.success(None, "ab_sr cookie更新已异步触发"))

    @app.route('/api/tasks/resume-paused')
    def trigger_resume_paused():
        resume_paused_tasks()
        return jsonify(ResponseFormatter.success(None, "暂停任务恢复已异步触发"))

def register_error_handlers(app):
    """全局错误处理"""
    @app.errorhandler(404)
    def not_found(error):
        return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "接口不存在")), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, "服务器内部错误")), 500

if __name__ == '__main__':
    # 获取运行配置
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

    app = create_app()
    log.info(f"启动应用，地址: http://{host}:{port}，调试模式: {'开启' if debug else '关闭'}")
    log.info(f"API文档地址: http://{host}:{port}/api/docs/")
    app.run(host=host, port=port, debug=debug)