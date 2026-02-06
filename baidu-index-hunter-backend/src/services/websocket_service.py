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
        # 发送 'task_update' 事件到所有连接的客户端
        # 如果需要定向发送给某个用户，可以在这里扩展逻辑（例如使用房间机制）
        socketio.emit('task_update', {
            'taskId': task_id,
            'progress': data.get('progress'),
            'status': data.get('status'),
            'completed_items': data.get('completed_items'),
            'total_items': data.get('total_items'),
            'error_message': data.get('error_message')
        })
        # log.debug(f"已通过 WebSocket 发送任务更新: {task_id}")
    except Exception as e:
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
