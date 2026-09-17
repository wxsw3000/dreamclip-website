#!/usr/bin/env bash
# DreamClip 生产/测试环境后台启动脚本 (Ubuntu 24.04 LTS)

echo "================================================================================"
echo "          🌌 DreamClip 角色宇宙与微服务平台启动脚本 (Linux/Ubuntu)"
echo "================================================================================"

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 停止旧进程
echo "[*] 正在检查并停止旧进程..."
pkill -f "mcp-base/run_server.py" 2>/dev/null
pkill -f "mcp-service-universe/run_server.py" 2>/dev/null
pkill -f "mcp-portal/run_server.py" 2>/dev/null
sleep 1

# 启动 Base (8000)
echo "[1/3] 启动 DreamClip-Base (Port 8000)..."
nohup python3 "$BASE_DIR/mcp-base/run_server.py" > "$BASE_DIR/base.log" 2>&1 &
sleep 2

# 启动 Universe (8081)
echo "[2/3] 启动 DreamClip-Service-Universe (Port 8081)..."
nohup python3 "$BASE_DIR/mcp-service-universe/run_server.py" > "$BASE_DIR/universe.log" 2>&1 &
sleep 2

# 启动 Portal (3000)
echo "[3/3] 启动 DreamClip-Portal (Port 3000)..."
nohup python3 "$BASE_DIR/mcp-portal/run_server.py" > "$BASE_DIR/portal.log" 2>&1 &
sleep 1

echo "================================================================================"
echo "  ✅ 全部服务已在后台启动！"
echo "  🌐 统一门户:     http://localhost:3000"
echo "  🛡️ 核心底座:     http://localhost:8000"
echo "  📖 宇宙内容:     http://localhost:8081/docs"
echo "================================================================================"
