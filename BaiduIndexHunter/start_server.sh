#!/bin/bash

# 确保在脚本所在目录执行
cd "$(dirname "$0")"

# 设置Python路径
export PYTHONPATH=$PYTHONPATH:$(pwd)

# 默认端口
PORT=4000

# 解析命令行参数
while [[ $# -gt 0 ]]; do
  case $1 in
    -p|--port)
      PORT="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

# 检查端口是否被占用
if lsof -i:$PORT > /dev/null 2>&1; then
    echo "警告: 端口 $PORT 已被占用，尝试使用其他端口..."
    # 尝试找到一个可用端口
    for try_port in {5001..5010}; do
        if ! lsof -i:$try_port > /dev/null 2>&1; then
            PORT=$try_port
            echo "使用端口 $PORT 替代"
            break
        fi
    done
fi

# 启动Gunicorn服务器
echo "启动百度指数API服务器..."
gunicorn -w 4 -b 0.0.0.0:$PORT api_server:app --timeout 120 --daemon

# 检查是否成功启动
sleep 2
if pgrep -f "gunicorn.*api_server" > /dev/null; then
    echo "服务器已成功启动，监听端口$PORT"
    echo "API地址: http://localhost:$PORT/api/health"
else
    echo "服务器启动失败，请检查日志"
fi 