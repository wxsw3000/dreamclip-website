import httpx
import logging
from app.core.config import settings

logger = logging.getLogger("dreamclip.register")

async def register_to_base():
    """微服务启动时自动向 MagicStarPlatform 底座服务注册自身"""
    payload = {
        "service_code": "dreamclip",
        "service_name": "DreamClip 梦之厅",
        "tech_stack": "PYTHON",
        "base_url": f"http://127.0.0.1:{settings.SERVER_PORT}",
        "health_url": "/health",
        "docs_url": "/docs",
        "gateway_prefix": "/dreamclip",
        "category": "UNIVERSE",
        "version": settings.VERSION,
        "status": "ACTIVE",
        "description": "沉浸式梦之厅官网、情绪胶囊切片流、AVG 互动剧场与 DreamClip Studio 独立内容工坊"
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(f"{settings.BASE_SERVICE_URL}/api/v1/microservices/register", json=payload)
            if resp.status_code == 200:
                logger.info("Successfully registered dreamclip to MagicStarPlatform (%s)", settings.BASE_SERVICE_URL)
            else:
                logger.warning("MagicStarPlatform registration responded with status %s: %s", resp.status_code, resp.text)
    except Exception as e:
        logger.warning("Could not auto-register to MagicStarPlatform at %s (%s). Will continue running.", settings.BASE_SERVICE_URL, e)
