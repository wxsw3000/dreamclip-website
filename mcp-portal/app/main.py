import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
import httpx

from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("mcp-portal")

async def register_self_to_base():
    """向底座 (dreamclip-base / 8000) 自动注册门户框架服务自身"""
    if not settings.AUTO_REGISTER_TO_BASE:
        return
    
    register_url = f"{settings.BASE_SERVICE_URL.rstrip('/')}/api/v1/microservices/register"
    payload = {
        "service_code": "dreamclip-portal",
        "service_name": "DreamClip 统一主站与角色宇宙门户",
        "tech_stack": "PYTHON",
        "category": "BASE",
        "base_url": f"http://127.0.0.1:{settings.SERVER_PORT}",
        "health_url": "/health",
        "docs_url": "/docs",
        "description": "面向C端用户的角色宇宙沉浸门户、情绪胶囊阅读器、AVG游戏分发与AdSense广告合规主站"
    }
    
    for attempt in range(1, 4):
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.post(register_url, json=payload)
                if resp.is_success:
                    logger.info("Successfully registered dreamclip-portal to base (%s)", register_url)
                    return
                else:
                    logger.warning("Failed to register to base (status %s): %s", resp.status_code, resp.text)
        except Exception as e:
            logger.warning("Attempt %s/3 to register to base failed: %s", attempt, e)
        await asyncio.sleep(2)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("============================================================")
    logger.info("  %s 启动中...", settings.PROJECT_NAME)
    logger.info("  访问入口: \thttp://localhost:%s", settings.SERVER_PORT)
    logger.info("  连接底座: \thttp://127.0.0.1:8000")
    logger.info("  连接宇宙: \thttp://127.0.0.1:8081")
    logger.info("============================================================")
    
    asyncio.create_task(register_self_to_base())
    yield
    logger.info("DreamClip-Portal application shutdown complete.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="DreamClip 统一主站：角色宇宙、情绪胶囊深度阅读与AVG互动游戏分发中心。",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", summary="健康检查端点 (供底座心跳探测)")
def health():
    return {
        "status": "UP",
        "service": "dreamclip-portal",
        "version": settings.VERSION
    }

# ==================== 反向代理：底座接口 (/api/base/** & /api/v1/**) ====================
@app.api_route("/api/base/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@app.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_base(path: str, request: Request):
    target_url = f"{settings.BASE_SERVICE_URL.rstrip('/')}/api/v1/{path}"
    query_params = dict(request.query_params)
    headers = dict(request.headers)
    headers.pop("host", None)
    body = await request.body()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.request(
                method=request.method,
                url=target_url,
                params=query_params,
                content=body,
                headers=headers
            )
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=dict(resp.headers),
                media_type=resp.headers.get("content-type")
            )
    except Exception as e:
        logger.error("Proxy to base error: %s", e)
        return JSONResponse(status_code=502, content={"code": 502, "message": f"底座服务通信失败: {str(e)}"})

# ==================== 反向代理：宇宙与内容接口 (/api/universe/**) ====================
@app.api_route("/api/universe/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_universe(path: str, request: Request):
    target_url = f"{settings.UNIVERSE_SERVICE_URL.rstrip('/')}/api/v1/{path}"
    query_params = dict(request.query_params)
    headers = dict(request.headers)
    headers.pop("host", None)
    body = await request.body()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.request(
                method=request.method,
                url=target_url,
                params=query_params,
                content=body,
                headers=headers
            )
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=dict(resp.headers),
                media_type=resp.headers.get("content-type")
            )
    except Exception as e:
        logger.error("Proxy to universe error: %s", e)
        return JSONResponse(status_code=502, content={"code": 502, "message": f"角色宇宙内容服务通信失败: {str(e)}"})

# ==================== 反向代理：基座 SuperAdmin 控制台 (/admin) ====================
@app.api_route("/admin", methods=["GET"])
@app.api_route("/admin/", methods=["GET"])
async def proxy_admin_root():
    """管理后台首页直通"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{settings.BASE_SERVICE_URL.rstrip('/')}/")
        return Response(content=resp.content, status_code=resp.status_code, media_type="text/html")

@app.api_route("/admin/login", methods=["GET"])
@app.api_route("/admin/login/", methods=["GET"])
async def proxy_admin_login():
    """管理后台登录页直通"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{settings.BASE_SERVICE_URL.rstrip('/')}/login")
        return Response(content=resp.content, status_code=resp.status_code, media_type="text/html")

@app.get("/login", include_in_schema=False)
def portal_login_page():
    return serve_static_page("login.html")

# ==================== 反向代理：微服务 Swagger 文档中心 ====================
@app.get("/base/docs", include_in_schema=False)
async def proxy_base_docs():
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{settings.BASE_SERVICE_URL.rstrip('/')}/docs")
        return Response(content=resp.content, status_code=resp.status_code, media_type="text/html")

@app.get("/base/openapi.json", include_in_schema=False)
async def proxy_base_openapi():
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{settings.BASE_SERVICE_URL.rstrip('/')}/openapi.json")
        return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")

@app.get("/universe/docs", include_in_schema=False)
async def proxy_universe_docs():
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{settings.UNIVERSE_SERVICE_URL.rstrip('/')}/docs")
        return Response(content=resp.content, status_code=resp.status_code, media_type="text/html")

@app.get("/universe/openapi.json", include_in_schema=False)
async def proxy_universe_openapi():
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{settings.UNIVERSE_SERVICE_URL.rstrip('/')}/openapi.json")
        return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")

# ==================== 静态资源与页面路由 ====================
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

def serve_static_page(filename: str):
    file_path = os.path.join(static_dir, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/", include_in_schema=False)
def index_page():
    return serve_static_page("index.html")

@app.get("/capsule/{identifier}", include_in_schema=False)
def capsule_page(identifier: str):
    return serve_static_page("capsule.html")

@app.get("/universe/{identifier}", include_in_schema=False)
def universe_page(identifier: str):
    return serve_static_page("universe.html")

@app.get("/character/{identifier}", include_in_schema=False)
def character_page(identifier: str):
    return serve_static_page("character.html")

@app.get("/games", include_in_schema=False)
def games_page():
    return serve_static_page("games.html")

@app.get("/game/{chapter_code}", include_in_schema=False)
def game_play_page(chapter_code: str):
    return serve_static_page("game_play.html")

# AdSense 4 大必备合规页面
@app.get("/about", include_in_schema=False)
def about_page():
    return serve_static_page("about.html")

@app.get("/privacy", include_in_schema=False)
def privacy_page():
    return serve_static_page("privacy.html")

@app.get("/terms", include_in_schema=False)
def terms_page():
    return serve_static_page("terms.html")

@app.get("/contact", include_in_schema=False)
def contact_page():
    return serve_static_page("contact.html")

# 挂载独立的 H5 游戏静态目录
games_dir = os.path.join(static_dir, "games")
if not os.path.exists(games_dir):
    os.makedirs(games_dir, exist_ok=True)
app.mount("/games", StaticFiles(directory=games_dir), name="games")
