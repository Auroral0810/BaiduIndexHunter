#!/bin/bash

# 停止Gunicorn服务器
echo "停止百度指数API服务器..."
pkill -f "gunicorn.*api_server" || echo "没有找到运行中的服务器进程"

# 检查是否成功停止
sleep 2
if pgrep -f "gunicorn.*api_server" > /dev/null; then
    echo "服务器停止失败，尝试强制终止..."
    pkill -9 -f "gunicorn.*api_server"
    sleep 1
    if pgrep -f "gunicorn.*api_server" > /dev/null; then
        echo "无法停止服务器，请手动终止进程"
    else
        echo "服务器已强制终止"
    fi
else
    echo "服务器已成功停止"
fi 