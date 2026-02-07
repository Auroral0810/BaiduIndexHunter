#!/bin/bash
# ====================
# BaiduIndexHunter 2.0 源代码清理脚本
# 用途：清理开发过程中产生的临时文件，生成干净的交付代码
# 用法：chmod +x clean_for_delivery.sh && ./clean_for_delivery.sh
# ====================

set -e

echo "🧹 开始清理 BaiduIndexHunter 2.0 项目..."

# 获取脚本所在目录（项目根目录）
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/baidu-index-hunter-backend"
FRONTEND_DIR="$PROJECT_ROOT/baidu-index-hunter-frontend"

# ============================================================
# 后端清理
# ============================================================
echo ""
echo "📦 清理后端目录..."

# 1. 删除所有 __pycache__ 目录
find "$BACKEND_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo "   ✓ 已删除 __pycache__ 目录"

# 2. 删除所有 .pyc 文件
find "$BACKEND_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
echo "   ✓ 已删除 .pyc 文件"

# 3. 删除日志文件（保留 logs 目录）
rm -f "$BACKEND_DIR/logs/"*.log 2>/dev/null || true
echo "   ✓ 已删除日志文件"

# 4. 删除输出文件和检查点（保留目录结构）
rm -rf "$BACKEND_DIR/output/"* 2>/dev/null || true
mkdir -p "$BACKEND_DIR/output/checkpoints"
echo "   ✓ 已清空 output 目录"

# 5. 删除实际的 .env 配置文件（保留 .env.example）
rm -f "$BACKEND_DIR/config/.env" 2>/dev/null || true
rm -f "$BACKEND_DIR/.env" 2>/dev/null || true
echo "   ✓ 已删除敏感配置文件 .env"

# 6. 删除 .DS_Store (macOS)
find "$BACKEND_DIR" -type f -name ".DS_Store" -delete 2>/dev/null || true
echo "   ✓ 已删除 .DS_Store 文件"

# 7. 删除测试目录中的 __pycache__（已在步骤1处理）

# ============================================================
# 前端清理
# ============================================================
echo ""
echo "🎨 清理前端目录..."

# 1. 删除 node_modules（用户需要重新 npm install）
rm -rf "$FRONTEND_DIR/node_modules" 2>/dev/null || true
echo "   ✓ 已删除 node_modules（用户需执行 npm install）"

# 2. 删除构建产物
rm -rf "$FRONTEND_DIR/dist" 2>/dev/null || true
echo "   ✓ 已删除 dist 构建目录"

# 3. 删除 .DS_Store
find "$FRONTEND_DIR" -type f -name ".DS_Store" -delete 2>/dev/null || true
echo "   ✓ 已删除 .DS_Store 文件"

# 4. 删除实际的 .env 配置文件（保留 .env.example）
rm -f "$FRONTEND_DIR/.env" 2>/dev/null || true
echo "   ✓ 已删除敏感配置文件 .env"

# ============================================================
# 项目根目录清理
# ============================================================
echo ""
echo "📁 清理项目根目录..."

# 删除 .DS_Store
find "$PROJECT_ROOT" -maxdepth 1 -type f -name ".DS_Store" -delete 2>/dev/null || true
echo "   ✓ 已删除根目录 .DS_Store"

# ============================================================
# 完成
# ============================================================
echo ""
echo "✅ 清理完成！"
echo ""
echo "📋 清理摘要："
echo "   - 已删除：__pycache__、*.pyc、*.log、.DS_Store"
echo "   - 已清空：output/、node_modules/、dist/"
echo "   - 已删除：.env 敏感配置文件"
echo ""
echo "📦 现在可以打包交付："
echo "   zip -r BaiduIndexHunter2.0.zip BaiduIndexHunter2.0/"
echo ""
