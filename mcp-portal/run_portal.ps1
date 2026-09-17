[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  正在启动 制造能力平台 - 统一门户框架 (MCP-Portal)..." -ForegroundColor Green
Write-Host "  工作台入口: http://localhost:3000" -ForegroundColor Yellow
Write-Host "  单点登录页: http://localhost:3000/login" -ForegroundColor Yellow
Write-Host "  连接服务底座: http://localhost:8000" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 检测 3000 端口占用
$portConns = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($portConns) {
    Write-Host "检测到 3000 端口被占用，正在释放..." -ForegroundColor Yellow
    foreach ($c in $portConns) {
        if ($c.OwningProcess -and $c.OwningProcess -ne 0) {
            Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 1
}

python run_portal.py
