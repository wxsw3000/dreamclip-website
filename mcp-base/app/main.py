import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.core.security import get_password_hash
from app.core.scheduler import run_periodic_health_checks
from app.models import (
    SysUser, SysRole, SysMenu,
    SysTenant, SysMicroservice,
    SysDictType, SysDictData, SysConfig,
    sys_user_role, sys_role_menu
)
from app.api.v1.router import api_v1_router

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("mcp-base")

def init_db_and_seed_data():
    """初始化数据库表并注入基础种子数据 (包含内置 superadmin 与预制数据)"""
    # 1. 自动创建所有数据表
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 2. 检查并创建角色
        admin_role = db.query(SysRole).filter(SysRole.role_code == "ROLE_SUPER_ADMIN").first()
        if not admin_role:
            admin_role = SysRole(
                role_code="ROLE_SUPER_ADMIN",
                role_name="平台超级管理员",
                role_level=1,
                remark="拥有制造能力平台底座所有管理权限"
            )
            operator_role = SysRole(
                role_code="ROLE_OPERATOR",
                role_name="系统操作员",
                role_level=10,
                remark="微服务常规业务操作权限"
            )
            db.add_all([admin_role, operator_role])
            db.commit()
            db.refresh(admin_role)
            logger.info("Initialized system roles: ROLE_SUPER_ADMIN, ROLE_OPERATOR")

        # 3. 检查并创建内置 superadmin 账号
        superadmin = db.query(SysUser).filter(SysUser.username == settings.SUPERADMIN_USERNAME).first()
        if not superadmin:
            superadmin = SysUser(
                username=settings.SUPERADMIN_USERNAME,
                password_hash=get_password_hash(settings.SUPERADMIN_DEFAULT_PASSWORD),
                real_name=settings.SUPERADMIN_REAL_NAME,
                email=settings.SUPERADMIN_EMAIL,
                is_superadmin=1,
                tenant_code="SYSTEM",
                status="ACTIVE",
                remark="系统预置平台超级管理员"
            )
            superadmin.roles.append(admin_role)
            db.add(superadmin)
            db.commit()
            logger.info("Initialized SuperAdmin account: %s (password: %s)", settings.SUPERADMIN_USERNAME, settings.SUPERADMIN_DEFAULT_PASSWORD)

        # 4. 检查并创建通用系统字典
        dict_count = db.query(SysDictType).count()
        if dict_count == 0:
            dict_types = [
                SysDictType(dict_code="industry_type", dict_name="企业行业分类"),
                SysDictType(dict_code="tech_stack", dict_name="微服务技术栈"),
                SysDictType(dict_code="service_category", dict_name="微服务业务分类")
            ]
            dict_data = [
                SysDictData(dict_code="industry_type", data_label="光学制造", data_value="OPTICAL", sort_order=1),
                SysDictData(dict_code="industry_type", data_label="军工电子", data_value="ELECTRONICS", sort_order=2),
                SysDictData(dict_code="industry_type", data_label="机械加工", data_value="MACHINERY", sort_order=3),
                SysDictData(dict_code="industry_type", data_label="通用制造", data_value="GENERAL", sort_order=4),
                
                SysDictData(dict_code="tech_stack", data_label="Java (Spring Boot)", data_value="JAVA", sort_order=1),
                SysDictData(dict_code="tech_stack", data_label="Python (FastAPI/AI)", data_value="PYTHON", sort_order=2),
                SysDictData(dict_code="tech_stack", data_label="Go (Golang IoT)", data_value="GO", sort_order=3),
                SysDictData(dict_code="tech_stack", data_label="Node.js / Vue", data_value="NODEJS", sort_order=4),
                SysDictData(dict_code="tech_stack", data_label="C# / .NET", data_value="DOTNET", sort_order=5),
                
                SysDictData(dict_code="service_category", data_label="平台基座", data_value="BASE", sort_order=1),
                SysDictData(dict_code="service_category", data_label="角色宇宙与内容", data_value="UNIVERSE", sort_order=2),
                SysDictData(dict_code="service_category", data_label="独立AVG游戏", data_value="GAME", sort_order=3),
                SysDictData(dict_code="service_category", data_label="AI互动伴侣", data_value="AI", sort_order=4),
                SysDictData(dict_code="service_category", data_label="工具扩展", data_value="TOOL", sort_order=5)
            ]
            db.add_all(dict_types)
            db.add_all(dict_data)
            db.commit()
            logger.info("Initialized system dictionaries")

        # 5. 检查并创建系统全局参数
        cfg_count = db.query(SysConfig).count()
        if cfg_count == 0:
            configs = [
                SysConfig(config_key="sys.platform.name", config_name="平台系统全称", config_value="MagicStar 模块化配置平台 (Modular Configuration Platform)", is_system=1),
                SysConfig(config_key="sys.auth.jwt_expire_hours", config_name="JWT登录有效期(小时)", config_value="168", is_system=1),
                SysConfig(config_key="sys.health_check.interval_seconds", config_name="微服务心跳探测周期(秒)", config_value="20", is_system=1)
            ]
            db.add_all(configs)
            db.commit()
            logger.info("Initialized system global configurations")

        # 6. 检查并正式注册核心系统门户框架 (mcp-portal / 3000)
        portal_svc = db.query(SysMicroservice).filter(SysMicroservice.service_code == "mcp-portal").first()
        if not portal_svc:
            portal_svc = SysMicroservice(
                service_code="mcp-portal",
                service_name="MagicStar 统一应用门户与网关",
                tech_stack="PYTHON",
                base_url="http://127.0.0.1:3000",
                health_url="/health",
                docs_url="/docs",
                gateway_prefix="/portal",
                category="BASE",
                version="1.0.0",
                status="ACTIVE",
                description="MagicStar 模块化配置平台的统一路由网关、SSO 认证与微服务应用门户"
            )
            db.add(portal_svc)
            db.commit()
            logger.info("Initialized core microservice registration: mcp-portal (Port 3000)")

        # 7. 检查并正式注册服务底座与治理中心自身 (mcp-base / 8000)
        base_svc = db.query(SysMicroservice).filter(SysMicroservice.service_code == "mcp-base").first()
        if not base_svc:
            base_svc = SysMicroservice(
                service_code="mcp-base",
                service_name="MagicStar MCP 配置治理底座",
                tech_stack="PYTHON",
                base_url=f"http://127.0.0.1:{settings.SERVER_PORT}",
                health_url="/health",
                docs_url="/docs",
                gateway_prefix="/base",
                category="BASE",
                version="1.0.0",
                status="ACTIVE",
                health_status="HEALTHY",
                description="通用用户中心、多租户管理、微服务生命周期治理、20秒健康心跳巡检与统一SSO鉴权"
            )
            db.add(base_svc)
            db.commit()
            logger.info("Initialized core microservice registration: mcp-base (Port 8000)")

        # 8. 检查并正式注册业务微服务应用 (mcp-service-universe / 8081)
        universe_svc = db.query(SysMicroservice).filter(SysMicroservice.service_code == "mcp-service-universe").first()
        if not universe_svc:
            universe_svc = SysMicroservice(
                service_code="mcp-service-universe",
                service_name="DreamClip 角色宇宙",
                tech_stack="PYTHON",
                base_url="http://127.0.0.1:8081",
                health_url="/health",
                docs_url="/docs",
                gateway_prefix="/universe",
                category="UNIVERSE",
                version="1.0.0",
                status="ACTIVE",
                health_status="HEALTHY",
                description="沉浸式世界观、角色档案、情绪胶囊与 AVG 互动剧场的独立业务微服务应用"
            )
            db.add(universe_svc)
            db.commit()
            logger.info("Initialized core microservice registration: mcp-service-universe (Port 8081)")

    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动初始化与后台任务挂载"""
    logger.info("============================================================")
    logger.info("  %s 启动中...", settings.PROJECT_NAME)
    logger.info("============================================================")
    
    # 1. 初始化数据库与种子数据
    init_db_and_seed_data()
    
    # 2. 启动异步健康心跳轮询后台协程
    health_task = asyncio.create_task(run_periodic_health_checks(settings.HEALTH_CHECK_INTERVAL_SECONDS))
    
    logger.info("  服务端口: \thttp://localhost:%s", settings.SERVER_PORT)
    logger.info("  Swagger UI: \thttp://localhost:%s/docs", settings.SERVER_PORT)
    logger.info("  ReDoc UI:   \thttp://localhost:%s/redoc", settings.SERVER_PORT)
    logger.info("  SuperAdmin: \t%s / %s", settings.SUPERADMIN_USERNAME, settings.SUPERADMIN_DEFAULT_PASSWORD)
    logger.info("============================================================")
    
    yield
    
    # 优雅停机
    health_task.cancel()
    logger.info("Application shutdown complete.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="MagicStar MCP (Modular Configuration Platform) 模块化配置平台：纯粹通用的微服务治理中枢、多租户分配、统一SSO鉴权与异构微服务健康探测。",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# 跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["00.健康探活"])
def health():
    """标准健康探活端点"""
    return {"status": "UP", "service": "mcp-base", "platform": "MagicStar-MCP", "code": 200}

# 挂载 API V1 路由
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

# 挂载静态 Web 控制台
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", include_in_schema=False)
@app.get("/admin", include_in_schema=False)
def root():
    """根路径自动重定向到 SuperAdmin Web 控制台"""
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return RedirectResponse(url="/docs")

@app.get("/login", include_in_schema=False)
@app.get("/admin/login", include_in_schema=False)
def login_page(request: Request):
    """提供 MagicStar MCP 控制台独立登录界面或重定向至统一单点登录中心"""
    raw_host = request.headers.get("host", "").lower()
    if "dreamclip.cn" in raw_host:
        return RedirectResponse(url="https://login.dreamclip.cn/")
    login_file = os.path.join(static_dir, "login.html")
    if os.path.exists(login_file):
        return FileResponse(login_file)
    return RedirectResponse(url="/")
