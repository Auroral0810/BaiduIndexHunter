from utils.logger import log

# SocketIO 实例占位符 - 用于子进程中安全调用
_socketio = None

def emit_task_update(task_id, data):
    """
    通过 WebSocket 发送任务更新消息
    :param task_id: 任务ID
    :param data: 包含进度、状态等的信息字典
    """
    global _socketio
    
    # 如果 socketio 未初始化（比如在子进程中），跳过发送
    if _socketio is None:
        # log.debug(f"WebSocket 未初始化，跳过发送任务更新 (可能在子进程中)")
        return
    
    try:
        # 发送 'task_update' 事件到所有连接的客户端
        _socketio.emit('task_update', {
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
    global _socketio
    from flask_socketio import SocketIO
    
    _socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')
    _socketio.init_app(app)
    log.info("WebSocket 服务已初始化")
    return _socketio

def get_socketio():
    """获取 SocketIO 实例（用于需要直接访问的场景）"""
    return _socketio
