"""
主应用程序入口
"""
import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from utils.logger import log
from api.task_controller import register_task_blueprint
from api.statistics_controller import register_statistics_blueprint
from cookie_manager.cookie_manager import CookieManager
from utils.city_manager import CityManager

# 全局变量，用于确保区域数据只同步一次
_region_data_synced = False

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 允许跨域请求
    CORS(app)
    
    # 配置Swagger
    app.config['SWAGGER'] = {
        'title': 'Baidu Index Hunter API',
        'description': 'Baidu Index Hunter API文档',
        'version': '1.0.0',
        'uiversion': 3,
        'termsOfService': '',
        'hide_top_bar': True
    }
    Swagger(app)
    
    # 注册蓝图
    register_task_blueprint(app)
    register_statistics_blueprint(app)
    
    # 注册错误处理
    register_error_handlers(app)
    
    # 初始化数据
    init_data()
    
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
    
    try:
        # 初始化城市数据
        if not _region_data_synced:
            city_manager = CityManager()
            city_manager.sync_to_redis()
            _region_data_synced = True
            log.info("区域数据同步到Redis成功")
        
        # 初始化Cookie数据
        cookie_manager = CookieManager()
        cookie_manager.sync_to_redis()
        log.info("Cookie数据同步到Redis成功")
        
    except Exception as e:
        log.error(f"初始化数据失败: {e}")

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    # 运行应用
    app.run(host='0.0.0.0', port=5000, debug=True) 