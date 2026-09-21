[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  正在启动 制造能力平台 - 开放服务底座 (MCP-Base Python FastAPI)..." -ForegroundColor Green
Write-Host "  控制台入口: http://localhost:8000" -ForegroundColor Yellow
Write-Host "  原生API文档: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "  预置超级管理: superadmin / 123456" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan

# 检测 8000 端口占用
$portConns = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portConns) {
    Write-Host "检测到 8000 端口被占用，正在释放..." -ForegroundColor Yellow
    foreach ($c in $portConns) {
        if ($c.OwningProcess -and $c.OwningProcess -ne 0) {
            Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 1
}

python run_server.py
