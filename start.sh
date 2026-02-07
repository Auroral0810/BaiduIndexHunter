#!/bin/bash

echo "===== 启动百度指数猎手项目 ====="
echo "检查必要环境..."

# 检查是否安装了Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查是否安装了Node.js
if ! command -v npm &> /dev/null; then
    echo "错误: 未找到npm，请先安装Node.js"
    exit 1
fi

# 检查Redis服务
if ! command -v redis-cli &> /dev/null; then
    echo "警告: 未找到redis-cli，Redis可能未安装"
    echo "后端服务可能无法正常运行，请确保Redis服务已启动"
else
    if ! redis-cli ping &> /dev/null; then
        echo "警告: Redis服务未运行，尝试启动Redis..."
        if command -v brew &> /dev/null; then
            brew services start redis
        elif command -v systemctl &> /dev/null; then
            sudo systemctl start redis
        else
            echo "请手动启动Redis服务"
        fi
    else
        echo "Redis服务已运行"
    fi
fi

# 检查MySQL服务
echo "请确保MySQL服务已启动并配置正确"

# 启动后端
echo "正在启动后端服务..."
cd baidu-index-hunter-backend || exit
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate
echo "安装后端依赖..."
# pip install -r requirements.txt

# 设置环境变量
export FLASK_APP=app.py
export FLASK_ENV=development

# 后台启动Flask服务
echo "启动Flask服务..."
nohup python app.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "后端服务已启动，PID: $BACKEND_PID"
echo "后端日志: $(pwd)/backend.log"
deactivate

# 启动前端
cd ../baidu-index-hunter-frontend || exit
echo "安装前端依赖..."
npm install

echo "启动前端服务..."
npm run dev &
FRONTEND_PID=$!
echo "前端服务已启动，PID: $FRONTEND_PID"

cd ..
echo "===== 服务启动完成 ====="
echo "前端地址: http://localhost:8080"
echo "后端地址: http://localhost:5001"
echo "API文档: http://localhost:5001/api/docs/"
echo ""
echo "提示: 按Ctrl+C可以停止服务"

# 等待用户中断
trap "kill $BACKEND_PID $FRONTEND_PID; echo '已停止所有服务'; exit 0" INT
wait