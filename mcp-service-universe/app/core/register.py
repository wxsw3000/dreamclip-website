import httpx
import logging
from app.core.config import settings

logger = logging.getLogger("mcp-universe.register")

async def register_to_base():
    """微服务启动时自动向 Base 底座服务注册自身"""
    payload = {
        "service_code": "mcp-service-universe",
        "service_name": "角色宇宙与内容微服务",
        "tech_stack": "PYTHON",
        "base_url": f"http://127.0.0.1:{settings.SERVER_PORT}",
        "health_url": "/health",
        "docs_url": "/docs",
        "gateway_prefix": "/api/universe",
        "category": "UNIVERSE",
        "version": settings.VERSION,
        "status": "ACTIVE",
        "description": "提供世界观设定、角色档案立绘、情绪胶囊原创深度图文与AVG互动剧本元数据"
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(f"{settings.BASE_SERVICE_URL}/api/v1/microservices/register", json=payload)
            if resp.status_code == 200:
                logger.info("Successfully registered to Base Service (%s)", settings.BASE_SERVICE_URL)
            else:
                logger.warning("Base Service registration responded with status %s: %s", resp.status_code, resp.text)
    except Exception as e:
        logger.warning("Could not auto-register to Base Service at %s (%s). Will continue running.", settings.BASE_SERVICE_URL, e)
