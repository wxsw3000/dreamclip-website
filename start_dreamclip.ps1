# DreamClip 一键并发启动脚本 (PowerShell)
$Host.UI.RawUI.WindowTitle = "DreamClip Microservice Runner"
Clear-Host

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "             🌌 DreamClip 角色宇宙与微服务平台一键启动 (PowerShell)" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

$root = $PSScriptRoot

Write-Host "[1/3] 正在启动 DreamClip-Base 核心底座 (Port 8000)..." -ForegroundColor Yellow
Start-Process cmd -ArgumentList "/k cd /d `"$root\mcp-base`" && python run_server.py"
Start-Sleep -Seconds 2

Write-Host "[2/3] 正在启动 DreamClip-Service-Universe 角色与内容微服务 (Port 8081)..." -ForegroundColor Yellow
Start-Process cmd -ArgumentList "/k cd /d `"$root\mcp-service-universe`" && python run_server.py"
Start-Sleep -Seconds 2

Write-Host "[3/3] 正在启动 DreamClip-Portal 统一主门户 (Port 3000)..." -ForegroundColor Yellow
Start-Process cmd -ArgumentList "/k cd /d `"$root\mcp-portal`" && python run_server.py"
Start-Sleep -Seconds 1

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Green
Write-Host "  ✨ DreamClip 全部核心微服务已并发启动！" -ForegroundColor Green
Write-Host ""
Write-Host "  🌐 统一主门户入口:     http://127.0.0.1:3000" -ForegroundColor White
Write-Host "  🛡️ 核心底座管理中心:   http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  📖 角色宇宙接口文档:   http://127.0.0.1:8081/docs" -ForegroundColor White
Write-Host ""
Write-Host "  📄 Google AdSense 合规必备页面:" -ForegroundColor Gray
Write-Host "     • 关于我们:         http://127.0.0.1:3000/about" -ForegroundColor Gray
Write-Host "     • 隐私政策:         http://127.0.0.1:3000/privacy" -ForegroundColor Gray
Write-Host "     • 服务条款:         http://127.0.0.1:3000/terms" -ForegroundColor Gray
Write-Host "     • 联系我们:         http://127.0.0.1:3000/contact" -ForegroundColor Gray
Write-Host "================================================================================" -ForegroundColor Green
