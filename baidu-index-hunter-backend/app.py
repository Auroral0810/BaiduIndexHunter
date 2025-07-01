"""
百度指数爬虫后端应用入口
"""
import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger, swag_from
from utils.logger import log
# 导入API蓝图
from api.cookie_controller import register_admin_cookie_blueprint
from api.region_controller import register_region_blueprint
from api.task_controller import register_task_blueprint
from api.statistics_controller import register_statistics_blueprint
from api.config_api import config_bp
from constant.respond import ResponseCode, ResponseFormatter
from region_manager.region_manager import get_region_manager, RegionManager
from cookie_manager.cookie_manager import CookieManager
from db.config_manager import config_manager

# 全局变量，用于确保区域数据只同步一次
_region_data_synced = False
_cookie_data_synced = False
_config_initialized = False

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def create_app(config=None):
    """创建Flask应用"""
    global _region_data_synced
    global _cookie_data_synced
    global _config_initialized
    
    app = Flask(__name__)
    
    # 配置跨域
    CORS(app)
    
    # 配置Swagger
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,  # 所有接口
                "model_filter": lambda tag: True,  # 所有模型
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
            "version": "1.0.0",
            "contact": {
                "name": "API 支持",
                "email": "15968588744@163.com"
            }
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Token 认证，格式: Bearer {token}"
            }
        },
        "security": [
            {
                "Bearer": []
            }
        ]
    }
    
    Swagger(app, config=swagger_config, template=swagger_template)
    
    # 初始化配置（全局只初始化一次）
    if not _config_initialized:
        try:
            config_manager.refresh_cache()
            config_manager.init_default_configs()
            _config_initialized = True
            log.info("系统配置初始化成功")
        except Exception as e:
            log.error(f"初始化系统配置失败: {e}")
    
    # 同步区域数据到Redis（全局只同步一次）
    if not _region_data_synced:
        try:
            region_manager = get_region_manager()
            region_manager.sync_to_redis()
            _region_data_synced = True
            log.info("区域数据同步到Redis成功")
        except Exception as e:
            log.error(f"同步区域数据到Redis失败: {e}")
    else:
        log.info("区域数据已同步，跳过重复同步")
    
    # 同步Cookie数据到Redis（全局只同步一次）
    if not _cookie_data_synced:
        try:
            cookie_manager = CookieManager()
            cookie_manager.sync_to_redis()
            _cookie_data_synced = True
            log.info("Cookie数据同步到Redis成功")
        except Exception as e:
            log.error(f"同步Cookie数据到Redis失败: {e}")
        finally:
            cookie_manager.close()
    else:
        log.info("Cookie数据已同步，跳过重复同步")
    
    # 注册蓝图
    register_admin_cookie_blueprint(app)
    register_region_blueprint(app)
    register_task_blueprint(app)
    register_statistics_blueprint(app)
    app.register_blueprint(config_bp)  # 注册配置API蓝图
    
    # 全局错误处理
    register_error_handlers(app)
    
    # 初始化数据
    init_data()
    
    # 首页路由
    @app.route('/')
    def index():
        """API首页"""
        return jsonify(ResponseFormatter.success({
            "name": "百度指数爬虫API",
            "version": "1.0.0",
            "docs": "/api/docs/"
        }, "欢迎使用百度指数爬虫API"))
    
    # 健康检查路由
    @app.route('/health')
    def health_check():
        """健康检查接口"""
        return jsonify(ResponseFormatter.success({
            "status": "UP",
            "timestamp": str(datetime.now())
        }))
        
    return app

def register_error_handlers(app):
    """注册错误处理"""
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'code': 10404,
            'msg': '接口不存在',
            'data': None
        }), 404
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            'code': 10500,
            'msg': '服务器内部错误',
            'data': None
        }), 500

def init_data():
    """初始化数据"""
    global _region_data_synced
    global _cookie_data_synced
    global _config_initialized
    
    try:
        # 初始化系统配置
        if not _config_initialized:
            config_manager.refresh_cache()
            config_manager.init_default_configs()
            _config_initialized = True
            log.info("系统配置初始化成功")
        
        # 初始化城市数据
        if not _region_data_synced:
            region_manager = get_region_manager()
            region_manager.sync_to_redis()
            _region_data_synced = True
            log.info("区域数据同步到Redis成功")
        
        # 初始化Cookie数据
        if not _cookie_data_synced:
            cookie_manager = CookieManager()
            cookie_manager.sync_to_redis()
            _cookie_data_synced = True
            log.info("Cookie数据同步到Redis成功")
            cookie_manager.close()
        
    except Exception as e:
        log.error(f"初始化数据失败: {e}")

if __name__ == '__main__':
    from datetime import datetime
    import os
    
    # 获取环境变量或使用默认值
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    
    # 在调试模式下，通过设置环境变量来控制是否跳过数据同步
    if debug and os.environ.get('SKIP_DATA_SYNC', 'false').lower() == 'true':
        _region_data_synced = True
        _cookie_data_synced = True
        log.info("调试模式：已设置跳过数据同步")
    
    app = create_app()
    log.info(f"启动应用，地址: http://{host}:{port}，调试模式: {'开启' if debug else '关闭'}")
    log.info(f"API文档地址: http://{host}:{port}/api/docs/")
    app.run(host=host, port=port, debug=debug) 