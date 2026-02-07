#!/usr/bin/env bash
# ============================================================================
# BaiduIndexHunter - 一键启动脚本
# 检查环境 → 安装依赖（如缺失）→ 启动后端 + 前端
# ============================================================================

set -e

# 获取项目根目录（脚本所在目录的父目录，或脚本所在目录即根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
BACKEND_DIR="$PROJECT_ROOT/baidu-index-hunter-backend"
FRONTEND_DIR="$PROJECT_ROOT/baidu-index-hunter-frontend"
VENV_DIR="$BACKEND_DIR/venv"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ----------------------------------------------------------------------------
# 1. 环境检查
# ----------------------------------------------------------------------------
check_env() {
    log_info "检查运行环境..."

    # Python 3.11+
    if command -v python3 &>/dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &>/dev/null; then
        PYTHON_CMD="python"
    else
        log_error "  ✗ 未找到 Python，请安装 Python 3.11+"
        exit 1
    fi
    PY_OK=$("$PYTHON_CMD" -c 'import sys; print("ok" if sys.version_info >= (3, 11) else "fail")' 2>/dev/null || echo "fail")
    if [[ "$PY_OK" == "ok" ]]; then
        log_info "  ✓ Python $("$PYTHON_CMD" --version 2>&1)"
    else
        log_error "  ✗ 需要 Python 3.11+，当前: $("$PYTHON_CMD" --version 2>&1)"
        exit 1
    fi

    # Node.js 18+
    if command -v node &>/dev/null; then
        NODE_VER=$(node -v 2>/dev/null | sed 's/v//' | cut -d. -f1)
        if [[ "$NODE_VER" -ge 18 ]] 2>/dev/null; then
            log_info "  ✓ Node.js $(node -v)"
        else
            log_error "  ✗ 需要 Node.js 18+，当前: $(node -v)"
            exit 1
        fi
    else
        log_error "  ✗ 未找到 Node.js，请安装 Node.js 18+"
        exit 1
    fi

    # Redis
    if command -v redis-cli &>/dev/null; then
        if redis-cli ping &>/dev/null; then
            log_info "  ✓ Redis 已运行 (redis-cli ping -> PONG)"
        else
            log_warn "  ⚠ Redis 未运行或无法连接，请先启动 Redis"
        fi
    elif command -v memurai-cli &>/dev/null; then
        if memurai-cli ping &>/dev/null; then
            log_info "  ✓ Memurai/Redis 已运行"
        else
            log_warn "  ⚠ Memurai 未运行或无法连接，请先启动 Memurai"
        fi
    else
        log_warn "  ⚠ 未找到 redis-cli 或 memurai-cli，请确保 Redis 已安装并运行"
    fi

    # MySQL（仅检查命令存在）
    if command -v mysql &>/dev/null; then
        log_info "  ✓ MySQL 客户端已安装"
    else
        log_warn "  ⚠ 未找到 mysql 命令，请确保 MySQL 8.0+ 已安装"
    fi

    # 后端 .env
    if [[ -f "$BACKEND_DIR/config/.env" ]]; then
        log_info "  ✓ 后端 .env 已配置"
    else
        log_error "  ✗ 未找到 $BACKEND_DIR/config/.env"
        log_error "    请复制 config/.env.example 为 config/.env 并填写 MYSQL_PASSWORD、API_SECRET_KEY"
        exit 1
    fi
}

# ----------------------------------------------------------------------------
# 2. 安装/检查依赖
# ----------------------------------------------------------------------------
setup_deps() {
    log_info "检查并安装依赖..."

    # 后端：虚拟环境
    if [[ ! -d "$VENV_DIR" ]]; then
        log_info "  创建 Python 虚拟环境..."
        "$PYTHON_CMD" -m venv "$VENV_DIR"
    fi

    log_info "  激活虚拟环境并安装后端依赖..."
    source "$VENV_DIR/bin/activate"
    pip install -q -r "$BACKEND_DIR/requirements.txt" 2>/dev/null || {
        log_warn "  使用国内镜像安装..."
        pip install -q -r "$BACKEND_DIR/requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple
    }

    # 前端：node_modules
    if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
        log_info "  安装前端依赖..."
        (cd "$FRONTEND_DIR" && npm install)
    else
        log_info "  ✓ 前端 node_modules 已存在"
    fi
}

# ----------------------------------------------------------------------------
# 3. 启动服务
# ----------------------------------------------------------------------------
BACKEND_PID=""

cleanup() {
    trap - SIGINT SIGTERM EXIT
    if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        log_info "停止后端服务 (PID: $BACKEND_PID)..."
        kill "$BACKEND_PID" 2>/dev/null || true
        wait "$BACKEND_PID" 2>/dev/null || true
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

start_services() {
    log_info "启动后端服务..."
    cd "$BACKEND_DIR"
    source "$VENV_DIR/bin/activate"
    "$PYTHON_CMD" app.py &
    BACKEND_PID=$!
    cd "$PROJECT_ROOT"

    # 等待后端就绪
    log_info "等待后端就绪..."
    for i in $(seq 1 30); do
        if (command -v curl &>/dev/null && curl -sf http://localhost:5001/api/health >/dev/null) || \
           (command -v wget &>/dev/null && wget -q -O /dev/null http://localhost:5001/api/health 2>/dev/null); then
            log_info "  ✓ 后端已启动: http://localhost:5001"
            break
        fi
        sleep 0.5
        [[ $i -eq 30 ]] && log_warn "后端健康检查超时，可能仍在启动中"
    done

    log_info "启动前端服务..."
    log_info "----------------------------------------"
    log_info "后端: http://localhost:5001"
    log_info "API 文档: http://localhost:5001/api/docs/"
    log_info "前端: http://localhost:5173/"
    log_info "按 Ctrl+C 停止服务"
    log_info "----------------------------------------"
    cd "$FRONTEND_DIR" && npm run dev
}

# ----------------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------------
main() {
    cd "$PROJECT_ROOT"
    log_info "BaiduIndexHunter 2.0 启动脚本"
    log_info "项目根目录: $PROJECT_ROOT"
    echo ""

    check_env
    echo ""
    setup_deps
    echo ""
    start_services
}

main "$@"
