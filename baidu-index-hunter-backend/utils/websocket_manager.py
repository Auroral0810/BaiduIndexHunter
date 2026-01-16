from flask_socketio import SocketIO
from utils.logger import log

# 初始化 SocketIO 实例
# async_mode='eventlet' 配合 eventlet 库使用，提供更好的并发性能
# cors_allowed_origins="*" 允许所有来源的连接，实际生产环境建议配置为前端域名
socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')

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
    return socketio
