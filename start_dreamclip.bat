@echo off
chcp 65001 >nul
cd /d "%~dp0"
cls
echo ================================================================================
echo             MagicStar & DreamClip 微服务平台一键启动 (v2.0)
echo ================================================================================
echo.

echo [1/2] 正在启动 MagicStarPlatform 平台底座 (Port 8000)...
start "MagicStarPlatform [8000]" cmd /k "cd /d "%~dp0magicstar-platform" && python run_server.py"

ping 127.0.0.1 -n 3 >nul

echo [2/2] 正在启动 DreamClip 梦之厅业务微服务 (Port 8081)...
start "DreamClip-Service [8081]" cmd /k "cd /d "%~dp0dreamclip-service" && python run_server.py"

echo.
echo ================================================================================
echo   ✨ 全部核心服务已并发启动！
echo.
echo   [梦之厅公众主站]   http://127.0.0.1:8081
echo   [梦之厅内容工坊]   http://127.0.0.1:8081/studio
echo   [PortalOS 平台桌面] http://127.0.0.1:8000/portal
echo   [平台底座治理中心] http://127.0.0.1:8000/admin
echo   [SSO 单点登录中心] http://127.0.0.1:8000/login
echo.
echo   [Swagger 接口文档]
echo   * 平台底座 API:    http://127.0.0.1:8000/docs
echo   * 梦之厅业务 API:  http://127.0.0.1:8081/docs
echo ================================================================================
pause
