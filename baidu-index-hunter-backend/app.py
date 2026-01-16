"""
百度指数爬虫API服务
"""
import os
import sys
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger, swag_from
from utils.logger import log
# 导入API蓝图
from api.cookie_controller import register_admin_cookie_blueprint
from api.region_controller import register_region_blueprint
from api.task_controller import register_task_blueprint
from api.statistics_controller import register_statistics_blueprint
from api.statistics import register_statistics_bp
from api.config_api import config_bp
from api.word_check_controller import register_word_check_blueprint
from utils.websocket_manager import init_socketio
from constant.respond import ResponseCode, ResponseFormatter
from region_manager.region_manager import get_region_manager, RegionManager
from cookie_manager.cookie_manager import CookieManager
from db.config_manager import config_manager
import threading
import time
import schedule
# 在文件顶部导入统一日志
from utils.logger import setup_unified_logger, setup_flask_request_logging, log_database_operation, log_task_operation

# 全局变量，用于确保区域数据只同步一次
_region_data_synced = False
_cookie_data_synced = False
_config_initialized = False

# 任务配置
TASK_CONFIG = {
    'max_concurrent_tasks': int(os.getenv('MAX_CONCURRENT_TASKS', 20)),  # 最大并发任务数，增加到20
    'task_queue_check_interval': int(os.getenv('TASK_QUEUE_CHECK_INTERVAL', 5)),  # 任务队列检查间隔（秒），减少到5秒
    'default_task_priority': int(os.getenv('DEFAULT_TASK_PRIORITY', 5)),  # 默认任务优先级（1-10）
    'max_retry_count': int(os.getenv('MAX_RETRY_COUNT', 3)),  # 任务最大重试次数
    'retry_delay': int(os.getenv('RETRY_DELAY', 120)),  # 任务重试延迟（秒），减少到120秒
}

# Cookie检查配置
COOKIE_CHECK_CONFIG = {
    'check_interval': int(os.getenv('COOKIE_CHECK_INTERVAL', 180)),  # Cookie状态检查间隔（秒），默认5分钟
    'ab_sr_update_interval': int(os.getenv('AB_SR_UPDATE_INTERVAL', 3600)),  # ab_sr cookie更新间隔（秒），默认1小时
    'resume_task_check_interval': int(os.getenv('RESUME_TASK_CHECK_INTERVAL', 300)),  # 恢复任务检查间隔（秒），默认5分钟
}

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 定时任务线程
_scheduler_thread = None
_scheduler_running = False

@log_task_operation("cookie_status_check")
def check_cookie_status():
    """检查所有cookie的状态，解封可用的cookie"""
    try:
        log.info("开始检查cookie状态...")
        cookie_manager = CookieManager()
        result = cookie_manager.check_and_update_cookie_status()
        cookie_manager.close()
        
        available_count = result.get('available_count', 0)
        total_count = result.get('total_count', 0)
        updated_count = result.get('updated_count', 0)
        unlocked_accounts = result.get('unlocked_accounts', [])
        
        if updated_count > 0:
            log.info(f"Cookie状态检查完成: 已解封 {updated_count} 条记录，涉及 {len(unlocked_accounts)} 个账号")
            log.info(f"当前可用账号: {available_count}/{total_count}")
            
            # 如果有账号被解封，检查是否有需要恢复的任务
            if len(unlocked_accounts) > 0:
                log.info("检测到有账号被解封，立即检查是否有需要恢复的任务")
                resume_paused_tasks()
        else:
            log.info(f"Cookie状态检查完成: {available_count}/{total_count} 可用，无需解封")
    except Exception as e:
        log.error(f"检查cookie状态时出错: {e}")
        import traceback
        log.error(traceback.format_exc())

def update_ab_sr_cookies():
    """更新所有账号的ab_sr cookie"""
    try:
        # log.info("开始更新所有账号的ab_sr cookie...")
        cookie_manager = CookieManager()
        result = cookie_manager.update_ab_sr_for_all_accounts()
        cookie_manager.close()
        
        if 'error' in result:
            log.error(f"更新ab_sr cookie失败: {result['error']}")
            return
        
        # log.info(f"成功更新ab_sr cookie: 更新{result['updated_count']}个，新增{result['added_count']}个，失败{result['failed_count']}个")
        # 
        # 更新完成后重置cookie轮换器的缓存
        from cookie_manager.cookie_rotator import cookie_rotator
        cookie_rotator.reset_cache()
    except Exception as e:
        log.error(f"更新ab_sr cookie时出错: {e}")

def resume_paused_tasks():
    """恢复因cookie不足而暂停的任务"""
    try:
        log.info("检查是否有因cookie不足而暂停的任务...")
        
        # 检查可用cookie数量
        cookie_manager = CookieManager()
        cookie_manager.sync_to_redis()
        available_count = cookie_manager.get_redis_available_cookie_count()
        cookie_manager.close()
        
        if available_count <= 0:
            log.info("没有可用cookie，无法恢复任务")
            return
            
        log.info(f"当前有 {available_count} 个可用cookie，开始查找暂停的任务")
            
        # 查找状态为paused的任务
        from db.mysql_manager import MySQLManager
        from scheduler.task_scheduler import task_scheduler
        
        mysql = MySQLManager()
        # 修改SQL查询，使用更宽松的条件匹配所有暂停的任务
        query = """
            SELECT task_id, error_message, update_time FROM spider_tasks 
            WHERE status = 'paused'
            ORDER BY update_time DESC LIMIT 10
        """
        paused_tasks = mysql.fetch_all(query)
        
        if not paused_tasks:
            log.info("没有暂停的任务需要恢复")
            return
            
        log.info(f"找到 {len(paused_tasks)} 个暂停的任务")
        
        # 恢复任务
        resumed_count = 0
        for task in paused_tasks:
            task_id = task['task_id']
            error_message = task.get('error_message', '')
            update_time = task.get('update_time')
            
            log.info(f"任务 {task_id} 暂停于 {update_time}，错误信息: {error_message}")
            
            # 尝试恢复任务
            log.info(f"尝试恢复任务: {task_id}")
            result = task_scheduler.resume_task(task_id)
            
            if result:
                resumed_count += 1
                log.info(f"成功恢复任务: {task_id}")
            else:
                log.warning(f"恢复任务失败: {task_id}")
            
        log.info(f"任务恢复检查完成，成功恢复 {resumed_count}/{len(paused_tasks)} 个任务")
    except Exception as e:
        log.error(f"恢复暂停任务时出错: {e}")
        import traceback
        log.error(traceback.format_exc())

def run_scheduler():
    """运行定时任务调度器"""
    global _scheduler_running
    
    _scheduler_running = True
    # log.info("定时任务调度器已启动")
    
    # 立即执行一次初始化检查
    check_cookie_status()
    update_ab_sr_cookies()
    
    # 设置定时任务
    schedule.every(COOKIE_CHECK_CONFIG['check_interval']).seconds.do(check_cookie_status)
    schedule.every(COOKIE_CHECK_CONFIG['ab_sr_update_interval']).seconds.do(update_ab_sr_cookies)
    schedule.every(COOKIE_CHECK_CONFIG['resume_task_check_interval']).seconds.do(resume_paused_tasks)
    
    # 运行调度器
    while _scheduler_running:
        schedule.run_pending()
        time.sleep(1)
    
    log.info("定时任务调度器已停止")

def start_scheduler():
    """启动定时任务调度器线程"""
    global _scheduler_thread
    
    if _scheduler_thread is None or not _scheduler_thread.is_alive():
        _scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        _scheduler_thread.start()
        # log.info("定时任务调度器线程已启动")
    else:
        log.info("定时任务调度器线程已在运行中")

def stop_scheduler():
    """停止定时任务调度器线程"""
    global _scheduler_running
    
    _scheduler_running = False
    log.info("定时任务调度器已标记为停止")

def create_app(config=None):
    
    # 首先设置统一日志系统
    unified_log = setup_unified_logger()
    
    """创建Flask应用"""
    global _region_data_synced
    global _cookie_data_synced
    global _config_initialized
    
    app = Flask(__name__)
    # 设置Flask请求日志（这会统一HTTP请求日志格式）
    setup_flask_request_logging(app, unified_log)
    
    # 配置跨域
    CORS(app, supports_credentials=True)
    
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
            # log.info("系统配置初始化成功")
        except Exception as e:
            log.error(f"初始化系统配置失败: {e}")
    
    # 同步区域数据到Redis（全局只同步一次）
    if not _region_data_synced:
        try:
            region_manager = get_region_manager()
            region_manager.sync_to_redis()
            _region_data_synced = True
            # log.info("区域数据同步到Redis成功")
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
            # log.info("Cookie数据同步到Redis成功")
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
    # register_statistics_blueprint(app)
    register_statistics_bp(app)
    register_word_check_blueprint(app)
    app.register_blueprint(config_bp)  # 注册配置API蓝图
    
    # 全局错误处理
    register_error_handlers(app)
    
    # 初始化数据
    init_data()
    
    # 初始化 WebSocket
    socketio = init_socketio(app)
    
    # 启动定时任务调度器
    start_scheduler()
    
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
    @app.route('/api/health')
    def health_check():
        """健康检查接口"""
        return jsonify(ResponseFormatter.success({
            "status": "UP",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, "API服务正常"))
    
    # 添加cookie状态管理路由
    @app.route('/api/cookie/check')
    def check_cookies():
        """手动检查cookie状态"""
        check_cookie_status()
        return jsonify(ResponseFormatter.success({
            "status": "OK",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, "Cookie状态检查已触发"))
    
    @app.route('/api/cookie/update-ab-sr')
    def update_ab_sr():
        """手动更新ab_sr cookie"""
        update_ab_sr_cookies()
        return jsonify(ResponseFormatter.success({
            "status": "OK",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, "ab_sr cookie更新已触发"))
    
    @app.route('/api/tasks/resume-paused')
    def resume_paused():
        """手动恢复暂停的任务"""
        resume_paused_tasks()
        return jsonify(ResponseFormatter.success({
            "status": "OK",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, "暂停任务恢复已触发"))
        
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
            # log.info("系统配置初始化成功")
        
        # 初始化城市数据
        if not _region_data_synced:
            region_manager = get_region_manager()
            region_manager.sync_to_redis()
            _region_data_synced = True
            # log.info("区域数据同步到Redis成功")
        
        # 初始化Cookie数据
        if not _cookie_data_synced:
            cookie_manager = CookieManager()
            cookie_manager.sync_to_redis()
            _cookie_data_synced = True
            # log.info("Cookie数据同步到Redis成功")
            cookie_manager.close()
        
    except Exception as e:
        log.error(f"初始化数据失败: {e}")

if __name__ == '__main__':
    from datetime import datetime
    import os
    
    # 获取环境变量或使用默认值
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    # 在调试模式下，通过设置环境变量来控制是否跳过数据同步
    if debug and os.environ.get('SKIP_DATA_SYNC', 'false').lower() == 'true':
        _region_data_synced = True
        _cookie_data_synced = True
        log.info("调试模式：已设置跳过数据同步")
    
    app = create_app()
    log.info(f"启动应用，地址: http://{host}:{port}，调试模式: {'开启' if debug else '关闭'}")
    log.info(f"API文档地址: http://{host}:{port}/api/docs/")
    app.run(host=host, port=port, debug=debug) 