"""
百度指数爬虫后端应用入口
"""
from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger, swag_from

# 导入API蓝图
from api.cookie_controller import register_admin_cookie_blueprint
from constant.respond import ResponseCode, ResponseFormatter

def create_app(config=None):
    """创建Flask应用"""
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
    
    # 注册蓝图
    register_admin_cookie_blueprint(app)
    
    # 全局错误处理
    @app.errorhandler(404)
    def not_found(e):
        return jsonify(ResponseFormatter.error(ResponseCode.NOT_FOUND, "接口不存在")), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify(ResponseFormatter.error(ResponseCode.SERVER_ERROR, "服务器内部错误")), 500
    
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

if __name__ == '__main__':
    from datetime import datetime
    import os
    
    # 获取环境变量或使用默认值
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    
    app = create_app()
    print(f"启动应用，地址: http://{host}:{port}，调试模式: {'开启' if debug else '关闭'}")
    print(f"API文档地址: http://{host}:{port}/api/docs/")
    app.run(host=host, port=port, debug=debug) 