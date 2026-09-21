# MagicStarPlatform & DreamClip 一键并发启动脚本 (PowerShell)
$Host.UI.RawUI.WindowTitle = "MagicStar & DreamClip Platform Runner"
Clear-Host

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "       🏛️ MagicStarPlatform 平台底座 & 🌌 DreamClip 梦之厅一键启动 (v2.0)" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

$root = $PSScriptRoot

Write-Host "[1/2] 正在启动 MagicStarPlatform 平台底座 (Port 8000)..." -ForegroundColor Yellow
Start-Process cmd -ArgumentList "/k cd /d `"$root\magicstar-platform`" && python run_server.py"
Start-Sleep -Seconds 2

Write-Host "[2/2] 正在启动 DreamClip 梦之厅业务微服务 (Port 8081)..." -ForegroundColor Yellow
Start-Process cmd -ArgumentList "/k cd /d `"$root\dreamclip`" && python run_server.py"
Start-Sleep -Seconds 1

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Green
Write-Host "  ✨ 全部核心服务已并发启动！" -ForegroundColor Green
Write-Host ""
Write-Host "  🌌 梦之厅公众主站:     http://127.0.0.1:8081" -ForegroundColor White
Write-Host "  🎨 梦之厅内容工坊:     http://127.0.0.1:8081/studio" -ForegroundColor White
Write-Host "  📱 PortalOS 平台桌面:  http://127.0.0.1:8000/portal" -ForegroundColor White
Write-Host "  ⚙️ 平台底座治理中心:   http://127.0.0.1:8000/admin" -ForegroundColor White
Write-Host "  🔐 统一单点登录入口:   http://127.0.0.1:8000/login" -ForegroundColor White
Write-Host ""
Write-Host "  📖 Swagger 在线接口文档:" -ForegroundColor Gray
Write-Host "     • 平台底座 API:     http://127.0.0.1:8000/docs" -ForegroundColor Gray
Write-Host "     • 梦之厅业务 API:   http://127.0.0.1:8081/docs" -ForegroundColor Gray
Write-Host "================================================================================" -ForegroundColor Green
