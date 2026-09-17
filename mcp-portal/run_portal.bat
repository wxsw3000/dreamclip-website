@echo off
chcp 65001 >nul
title 制造能力平台 - 统一门户框架 (MCP-Portal)
echo ============================================================
echo   正在启动 制造能力平台 - 统一门户框架 (MCP-Portal)...
echo   访问入口: http://localhost:3000
echo   单点登录: http://localhost:3000/login
echo   连接底座: http://localhost:8000
echo ============================================================

python run_portal.py
pause
