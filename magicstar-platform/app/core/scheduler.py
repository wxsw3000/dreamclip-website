import asyncio
import time
import logging
from datetime import datetime
from typing import Optional
import httpx
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.microservice import SysMicroservice
from app.schemas.microservice import HealthProbeResult

logger = logging.getLogger("mcp-base.scheduler")

async def probe_single_service(service: SysMicroservice, db: Optional[Session] = None) -> HealthProbeResult:
    """探测单个微服务的健康状态"""
    # 拼接完整健康检查 URL
    base = service.base_url.rstrip("/")
    path = service.health_url.strip()
    if not path.startswith("/"):
        path = "/" + path
    full_url = f"{base}{path}"

    start_time = time.time()
    health_status = "DOWN"
    status_code = None
    error_msg = None
    details = {}
    
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(full_url)
            status_code = resp.status_code
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            
            if resp.is_success:
                health_status = "HEALTHY"
                try:
                    details = resp.json()
                except Exception:
                    details = {"body": resp.text[:200]}
            else:
                health_status = "UNHEALTHY"
                error_msg = f"HTTP状态码: {resp.status_code}"
    except httpx.ConnectError:
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        health_status = "DOWN"
        error_msg = "无法连接服务端点 (Connection Refused)"
    except httpx.TimeoutException:
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        health_status = "DOWN"
        error_msg = "请求超时 (>4.0s)"
    except Exception as e:
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        health_status = "DOWN"
        error_msg = f"连接异常: {str(e)}"

    # 如果传入了 db session 则就地持久化
    if db:
        service.health_status = health_status
        service.last_heartbeat = datetime.now()
        service.response_time_ms = elapsed_ms
        service.last_error_msg = error_msg
        db.commit()

    return HealthProbeResult(
        service_code=service.service_code,
        service_name=service.service_name,
        health_status=health_status,
        response_time_ms=elapsed_ms,
        status_code=status_code,
        error_msg=error_msg,
        details=details
    )

async def run_periodic_health_checks(interval_seconds: int = 20):
    """后台常驻协程：定时轮询探测所有已启用的微服务健康状态"""
    logger.info("Starting background microservice health check loop (interval: %ss)...", interval_seconds)
    while True:
        try:
            db = SessionLocal()
            try:
                services = db.query(SysMicroservice).filter(
                    SysMicroservice.is_deleted == 0,
                    SysMicroservice.status == "ACTIVE"
                ).all()
                for s in services:
                    await probe_single_service(s, db=db)
            finally:
                db.close()
        except Exception as e:
            logger.error("Error in health check background loop: %s", e)
            
        await asyncio.sleep(interval_seconds)
