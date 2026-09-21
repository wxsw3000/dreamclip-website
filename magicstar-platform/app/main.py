import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
import httpx
from sqlalchemy import text

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
logger = logging.getLogger("magicstar-platform")

def auto_migrate_db_columns():
    """自动检测并补齐数据表中新增的字段 (兼容 MySQL 与 SQLite)"""
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        for table_name, table in Base.metadata.tables.items():
            if table_name not in existing_tables:
                continue
            existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
            for col in table.columns:
                if col.name not in existing_cols:
                    col_type = col.type.compile(engine.dialect)
                    default_clause = ""
                    if col.default is not None and col.default.arg is not None:
                        default_clause = f" DEFAULT {col.default.arg}"
                    elif col.nullable:
                        default_clause = " DEFAULT NULL"
                    else:
                        default_clause = " DEFAULT 0"
                    
                    is_sqlite = (engine.dialect.name == "sqlite")
                    if is_sqlite:
                        alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}{default_clause}"
                    else:
                        alter_sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{col.name}` {col_type}{default_clause}"
                    
                    try:
                        with engine.begin() as conn:
                            conn.execute(text(alter_sql))
                        logger.info("Auto-migrated missing column: %s.%s (%s)", table_name, col.name, col_type)
                    except Exception as col_err:
                        logger.warning("Could not auto-add column %s.%s: %s", table_name, col.name, col_err)
    except Exception as e:
        logger.warning("Auto-migration check encountered error: %s", e)

def init_db_and_seed_data():
    """初始化数据库表并注入基础种子数据 (平台底座 + dreamclip 第一个业务节点)"""
    Base.metadata.create_all(bind=engine)
    auto_migrate_db_columns()

    db = SessionLocal()
    try:
        # 1. 检查并创建系统内置基础角色
        admin_role = db.query(SysRole).filter(SysRole.role_code == "ROLE_SUPER_ADMIN").first()
        if not admin_role:
            admin_role = SysRole(
                role_code="ROLE_SUPER_ADMIN",
                role_name="平台超级管理员",
                role_level=1,
                is_system=1,
                status="ACTIVE",
                remark="拥有全量微服务与底座治理最高控制权限 (系统内置/不可删除/全量授权)"
            )
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            logger.info("Initialized system role: ROLE_SUPER_ADMIN")
        else:
            if getattr(admin_role, "is_system", 0) != 1:
                admin_role.is_system = 1
                db.commit()

        operator_role = db.query(SysRole).filter(SysRole.role_code == "ROLE_OPERATOR").first()
        if not operator_role:
            operator_role = SysRole(
                role_code="ROLE_OPERATOR",
                role_name="系统运维操作员",
                role_level=10,
                is_system=1,
                status="ACTIVE",
                remark="微服务与底座常规业务运维操作权限 (系统内置/不可删除)"
            )
            db.add(operator_role)
            db.commit()
            db.refresh(operator_role)
            logger.info("Initialized system role: ROLE_OPERATOR")
        else:
            if getattr(operator_role, "is_system", 0) != 1:
                operator_role.is_system = 1
                db.commit()

        member_role = db.query(SysRole).filter(SysRole.role_code == "ROLE_MEMBER").first()
        if not member_role:
            member_role = SysRole(
                role_code="ROLE_MEMBER",
                role_name="平台标准注册会员",
                role_level=20,
                is_system=1,
                status="ACTIVE",
                remark="平台默认注册用户角色，享有门户与公开业务微服务访问权限 (系统内置/不可删除)"
            )
            db.add(member_role)
            db.commit()
            db.refresh(member_role)
            logger.info("Initialized system role: ROLE_MEMBER")
        else:
            if getattr(member_role, "is_system", 0) != 1:
                member_role.is_system = 1
                db.commit()

        # 2. 检查并创建内置 superadmin 账号
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
            logger.info("Initialized SuperAdmin account: %s", settings.SUPERADMIN_USERNAME)

        # 3. 检查并创建通用系统字典
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

        # 4. 检查并创建系统全局参数
        cfg_count = db.query(SysConfig).count()
        if cfg_count == 0:
            configs = [
                SysConfig(config_key="sys.platform.name", config_name="平台系统全称", config_value="MagicStarPlatform 平台底座", is_system=1),
                SysConfig(config_key="sys.auth.jwt_expire_hours", config_name="JWT登录有效期(小时)", config_value="168", is_system=1),
                SysConfig(config_key="sys.health_check.interval_seconds", config_name="微服务心跳探测周期(秒)", config_value="20", is_system=1)
            ]
            db.add_all(configs)
            db.commit()
            logger.info("Initialized system global configurations")

        # 5. 迁移与注册核心服务
        # 5.1 注册平台底座自身 (magicstar-platform)
        platform_svc = db.query(SysMicroservice).filter(
            SysMicroservice.service_code.in_(["magicstar-platform", "mcp-base"])
        ).first()
        if not platform_svc:
            platform_svc = SysMicroservice(
                service_code="magicstar-platform",
                service_name="MagicStarPlatform 平台底座",
                tech_stack="PYTHON",
                base_url=f"http://127.0.0.1:{settings.SERVER_PORT}",
                health_url="/health",
                docs_url="/docs",
                gateway_prefix="/base",
                category="BASE",
                version="1.0.0",
                status="ACTIVE",
                health_status="HEALTHY",
                description="统一网关、SSO 单点认证中心、PortalOS 平台桌面、用户角色权限与微服务生命周期治理"
            )
            db.add(platform_svc)
            db.commit()
            logger.info("Initialized core service registration: magicstar-platform")
        else:
            platform_svc.service_code = "magicstar-platform"
            platform_svc.service_name = "MagicStarPlatform 平台底座"
            platform_svc.base_url = f"http://127.0.0.1:{settings.SERVER_PORT}"
            db.commit()

        # 5.2 注册第 1 业务节点 (dreamclip-service)
        dreamclip_svc = db.query(SysMicroservice).filter(
            SysMicroservice.service_code.in_(["dreamclip-service", "dreamclip", "mcp-service-universe"])
        ).first()
        if not dreamclip_svc:
            dreamclip_svc = SysMicroservice(
                service_code="dreamclip-service",
                service_name="DreamClip 梦之厅业务微服务 (dreamclip-service)",
                tech_stack="PYTHON",
                base_url=settings.DREAMCLIP_SERVICE_URL,
                health_url="/health",
                docs_url="/docs",
                gateway_prefix="/dreamclip",
                category="UNIVERSE",
                version="1.0.0",
                status="ACTIVE",
                health_status="HEALTHY",
                description="沉浸式梦之厅官网、情绪胶囊切片流、AVG 互动剧场与 DreamClip Studio 独立内容工坊"
            )
            db.add(dreamclip_svc)
            db.commit()
            logger.info("Initialized core business registration: dreamclip-service (Port 8081)")
        else:
            dreamclip_svc.service_code = "dreamclip-service"
            dreamclip_svc.service_name = "DreamClip 梦之厅业务微服务 (dreamclip-service)"
            dreamclip_svc.base_url = settings.DREAMCLIP_SERVICE_URL
            dreamclip_svc.gateway_prefix = "/dreamclip"
            db.commit()

        # 清理多余的旧注册条目 (如 mcp-portal)
        for old_code in ["mcp-portal", "dreamclip", "mcp-service-universe"]:
            if old_code != "dreamclip-service":
                old_svc = db.query(SysMicroservice).filter(SysMicroservice.service_code == old_code).first()
                if old_svc and old_svc.id != dreamclip_svc.id:
                    db.delete(old_svc)
                    db.commit()

        # 6. 生成 APP 权限菜单节点
        app_menus_config = [
            ("magicstar-platform", "MagicStarPlatform 平台底座", "⭐", "/admin", 1),
            ("dreamclip-service", "DreamClip 梦之厅", "🌌", "http://127.0.0.1:8081/", 2)
        ]
        for code, name, icon, path, sort in app_menus_config:
            m = db.query(SysMenu).filter(SysMenu.service_code == code, SysMenu.menu_type == "APP", SysMenu.is_deleted == 0).first()
            if not m:
                m = SysMenu(
                    parent_id=0,
                    menu_name=name,
                    menu_type="APP",
                    path=path,
                    icon=icon,
                    service_code=code,
                    sort_order=sort,
                    is_visible=1
                )
                db.add(m)
            else:
                m.menu_name = name
                m.icon = icon
                m.path = path
        db.commit()

        # 7. 为系统角色赋予默认微服务应用权限
        platform_app = db.query(SysMenu).filter(SysMenu.service_code == "magicstar-platform", SysMenu.menu_type == "APP", SysMenu.is_deleted == 0).first()
        dreamclip_app = db.query(SysMenu).filter(SysMenu.service_code == "dreamclip-service", SysMenu.menu_type == "APP", SysMenu.is_deleted == 0).first()

        # 为 ROLE_OPERATOR 赋予底座治理与业务应用权限
        if operator_role:
            operator_role.menus = [m for m in [platform_app, dreamclip_app] if m]
            db.commit()

        # 为 ROLE_MEMBER 赋予 dreamclip-service 业务应用权限
        if member_role:
            member_role.menus = [m for m in [dreamclip_app] if m]
            db.commit()

    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动初始化与后台任务挂载"""
    logger.info("============================================================")
    logger.info("  %s 启动中...", settings.PROJECT_NAME)
    logger.info("============================================================")
    
    init_db_and_seed_data()
    health_task = asyncio.create_task(run_periodic_health_checks(settings.HEALTH_CHECK_INTERVAL_SECONDS))
    
    logger.info("  底座端口: \thttp://localhost:%s", settings.SERVER_PORT)
    logger.info("  PortalOS: \thttp://localhost:%s/portal", settings.SERVER_PORT)
    logger.info("  管理控制台: \thttp://localhost:%s/admin", settings.SERVER_PORT)
    logger.info("  Swagger UI: \thttp://localhost:%s/docs", settings.SERVER_PORT)
    logger.info("  SuperAdmin: \t%s / %s", settings.SUPERADMIN_USERNAME, settings.SUPERADMIN_DEFAULT_PASSWORD)
    logger.info("============================================================")
    
    yield
    
    health_task.cancel()
    logger.info("MagicStarPlatform application shutdown complete.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="MagicStarPlatform 平台底座：统一网关分流、SSO 认证中心、PortalOS 平台桌面、多租户与 IAM 权限体系及异构微服务治理中枢。",
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

static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

# ==================== 智能反向代理核心函数 ====================
async def forward_request(request: Request, target_url: str) -> Response:
    query_params = dict(request.query_params)
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    body = await request.body()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request(
                method=request.method,
                url=target_url,
                params=query_params,
                content=body,
                headers=headers
            )
            resp_headers = dict(resp.headers)
            resp_headers.pop("transfer-encoding", None)
            resp_headers.pop("content-encoding", None)
            
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=resp_headers,
                media_type=resp.headers.get("content-type")
            )
    except Exception as e:
        logger.error("Proxy error to %s: %s", target_url, e)
        return JSONResponse(status_code=502, content={"code": 502, "message": f"微服务通信失败: {str(e)}"})

# ==================== Host 虚拟主机智能分流中间件 ====================
@app.middleware("http")
async def host_virtual_routing_middleware(request: Request, call_next):
    path = request.url.path

    # 1. 优先放行所有底座后端 API 路由、静态资源及探活请求
    if path.startswith("/api/v1/") or path.startswith("/static/") or path == "/health" or path == "/docs" or path == "/openapi.json":
        return await call_next(request)

    raw_host = request.headers.get("host", "")
    host = raw_host.split(":")[0].strip().lower()

    # 2. 独立子域名：login.dreamclip.cn / sso.dreamclip.cn / auth.dreamclip.cn -> 统一单点登录与注册
    if host in ["login.dreamclip.cn", "sso.dreamclip.cn", "auth.dreamclip.cn"]:
        if path in ["/", "", "/login", "/register", "/sso", "/auth"]:
            return FileResponse(os.path.join(static_dir, "login.html"))
        file_path = os.path.join(static_dir, path.lstrip("/"))
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_dir, "login.html"))

    # 3. 独立子域名：portal.dreamclip.cn / workbench.dreamclip.cn -> PortalOS 应用桌面 (未登录拦截跳转)
    if host in ["portal.dreamclip.cn", "workbench.dreamclip.cn"]:
        token = request.cookies.get("mcp_token") or request.cookies.get("dreamclip_token")
        if not token and path in ["/", "", "/portal", "/workbench"]:
            return RedirectResponse(url="https://login.dreamclip.cn/?redirect=https://portal.dreamclip.cn/", status_code=302)
        if path in ["/", "", "/portal", "/workbench"]:
            return FileResponse(os.path.join(static_dir, "portal.html"))
        file_path = os.path.join(static_dir, path.lstrip("/"))
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return await call_next(request)

    # 4. 独立子域名：base.dreamclip.cn / admin.dreamclip.cn -> 直达 SuperAdmin 控制台 (未登录拦截跳转)
    if host in ["base.dreamclip.cn", "admin.dreamclip.cn"]:
        token = request.cookies.get("mcp_token") or request.cookies.get("dreamclip_token")
        if not token and path in ["/", "", "/admin", "/base"]:
            return RedirectResponse(url="https://login.dreamclip.cn/?redirect=https://base.dreamclip.cn/", status_code=302)
        if path in ["/", "", "/admin", "/base"]:
            return FileResponse(os.path.join(static_dir, "index.html"))
        return await call_next(request)

    # 5. 主站子域名：dreamclip.cn / www.dreamclip.cn / universe.dreamclip.cn -> 转发至 dreamclip 业务节点
    if host in ["dreamclip.cn", "www.dreamclip.cn", "universe.dreamclip.cn", "game.dreamclip.cn", "games.dreamclip.cn"]:
        target_url = f"{settings.DREAMCLIP_SERVICE_URL.rstrip('/')}{path}"
        return await forward_request(request, target_url)

    # 6. 业务主站路径智能代理转发 (梦之厅、内容工坊、AVG游戏、胶囊阅读、合规页面)
    business_prefixes = ["/studio", "/capsule", "/character", "/games", "/game", "/about", "/privacy", "/terms", "/contact", "/universe"]
    if any(path == prefix or path.startswith(prefix + "/") or path.startswith(prefix) for prefix in business_prefixes):
        target_url = f"{settings.DREAMCLIP_SERVICE_URL.rstrip('/')}{path}"
        return await forward_request(request, target_url)

    return await call_next(request)

@app.get("/health", tags=["00.健康探活"])
def health():
    """标准健康探活端点"""
    return {"status": "UP", "service": "magicstar-platform", "platform": "MagicStarPlatform", "code": 200}

# ==================== 路径模式反向代理：dreamclip 业务接口 ====================
@app.api_route("/api/dreamclip/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@app.api_route("/api/universe/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_dreamclip(path: str, request: Request):
    target_url = f"{settings.DREAMCLIP_SERVICE_URL.rstrip('/')}/api/v1/{path}"
    return await forward_request(request, target_url)

# 挂载 API V1 路由
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

# 挂载静态 Web 资源
app.mount("/static", StaticFiles(directory=static_dir), name="static")

def serve_static_file(filename: str):
    file_path = os.path.join(static_dir, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(static_dir, "portal.html"))

@app.get("/", include_in_schema=False)
def root():
    """根路径默认直达 PortalOS 应用桌面"""
    return serve_static_file("portal.html")

@app.get("/portal", include_in_schema=False)
@app.get("/portal/{path:path}", include_in_schema=False)
@app.get("/workbench", include_in_schema=False)
def portal_desktop():
    """PortalOS 统一应用桌面"""
    return serve_static_file("portal.html")

@app.get("/login", include_in_schema=False)
@app.get("/sso", include_in_schema=False)
@app.get("/auth", include_in_schema=False)
def login_page():
    """SSO 统一单点登录页"""
    return serve_static_file("login.html")

@app.get("/register", include_in_schema=False)
def register_page():
    """统一注册页"""
    return serve_static_file("register.html")

@app.get("/admin", include_in_schema=False)
@app.get("/base", include_in_schema=False)
def admin_page():
    """MagicStar 平台底座管理控制台"""
    return serve_static_file("index.html")
