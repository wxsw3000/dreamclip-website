#!/bin/bash
echo "================================================================================"
echo "       🏛️ MagicStarPlatform 平台底座 & 🌌 DreamClip 梦之厅一键启动 (v2.0)"
echo "================================================================================"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[1/2] 正在启动 MagicStarPlatform 平台底座 (Port 8000)..."
(cd "$ROOT_DIR/magicstar-platform" && python run_server.py) &
PID_PLATFORM=$!

sleep 2

echo "[2/2] 正在启动 DreamClip 梦之厅业务微服务 (Port 8081)..."
(cd "$ROOT_DIR/dreamclip" && python run_server.py) &
PID_DREAMCLIP=$!

echo "服务已在后台运行 (Platform PID: $PID_PLATFORM, DreamClip PID: $PID_DREAMCLIP)"
wait
