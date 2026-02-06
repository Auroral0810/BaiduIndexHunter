from flask_socketio import SocketIO
from src.core.logger import log
from datetime import datetime

# 初始化 SocketIO 实例
# async_mode='threading' 提供最广的平台兼容性
# cors_allowed_origins="*" 允许所有来源的连接，实际生产环境建议配置为前端域名
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')

def emit_task_update(task_id, data):
    """
    通过 WebSocket 发送任务更新消息
    :param task_id: 任务ID
    :param data: 包含进度、状态等的信息字典
    """
    try:
        # 只有在 SocketIO 已初始化且服务器存在时才发送
        if socketio.server is None:
            # log.debug("WebSocket 尚未初始化，跳过发送")
            return
            
        # 发送 'task_update' 事件到所有连接的客户端
        socketio.emit('task_update', {
            'taskId': task_id,
            'progress': data.get('progress'),
            'status': data.get('status'),
            'completed_items': data.get('completed_items'),
            'total_items': data.get('total_items'),
            'error_message': data.get('error_message')
        })
    except Exception as e:
        # 避免在非关键路径上抛出异常，仅记录日志
        if "NoneType" not in str(e):
            log.error(f"WebSocket 发送更新失败: {e}")

def init_socketio(app):
    """
    初始化并将 SocketIO 绑定到 Flask 应用
    """
    socketio.init_app(app)
    log.info("WebSocket 服务已初始化")
    
    # 注册日志推送器到统一日志系统
    from src.core.logger import set_log_pusher
    
    def log_pusher(log_data):
        """将日志推送到所有连接的客户端"""
        try:
            socketio.emit('system_log', log_data)
        except Exception as e:
            # 避免在日志推送器中记录普通错误日志，防止死循环
            print(f"WebSocket 日志推送失败: {e}")
            
    set_log_pusher(log_pusher)
    log.info("实时显示系统日志已开启")

    @socketio.on('connect')
    def handle_connect():
        emit_task_update('system', {'status': 'connected'})
        # 发送一条欢迎日志，确认连接成功
        log_pusher({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "level": "INFO",
            "name": "System",
            "function": "handle_connect",
            "line": "0",
            "message": "Client connected to real-time log stream. Waiting for system events..."
        })
    
    return socketio
