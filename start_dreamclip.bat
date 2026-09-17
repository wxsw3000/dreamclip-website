@echo off
chcp 65001 >nul
cd /d "%~dp0"
cls
echo ================================================================================
echo             DreamClip Microservice Platform Launcher (v1.0)
echo ================================================================================
echo.

echo [1/3] Starting DreamClip-Base (Port 8000)...
start "DreamClip-Base [8000]" cmd /k "cd /d "%~dp0mcp-base" && python run_server.py"

ping 127.0.0.1 -n 3 >nul

echo [2/3] Starting DreamClip-Service-Universe (Port 8081)...
start "DreamClip-Universe [8081]" cmd /k "cd /d "%~dp0mcp-service-universe" && python run_server.py"

ping 127.0.0.1 -n 3 >nul

echo [3/3] Starting DreamClip-Portal (Port 3000)...
start "DreamClip-Portal [3000]" cmd /k "cd /d "%~dp0mcp-portal" && python run_server.py"

echo.
echo ================================================================================
echo   DreamClip Services Launched Successfully!
echo.
echo   [Portal Web]     http://127.0.0.1:3000
echo   [Base Auth]      http://127.0.0.1:8000
echo   [Universe API]   http://127.0.0.1:8081/docs
echo.
echo   [AdSense Pages]
echo   * About Us:      http://127.0.0.1:3000/about
echo   * Privacy:       http://127.0.0.1:3000/privacy
echo   * Terms:         http://127.0.0.1:3000/terms
echo   * Contact:       http://127.0.0.1:3000/contact
echo ================================================================================
pause
