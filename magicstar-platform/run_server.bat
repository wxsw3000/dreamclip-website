@echo off
chcp 65001 >nul
title 制造能力平台 - 开放服务底座 (MCP-Base)
echo ============================================================
echo   正在启动 制造能力平台 - 开放服务底座 (MCP-Base Python FastAPI)...
echo   访问地址: http://localhost:8000
echo   API 文档: http://localhost:8000/docs
echo   超管账号: superadmin / 123456
echo ============================================================

python run_server.py
pause
