from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    get_current_user_payload, get_optional_user_payload
)
from app.models.user import SysUser, SysRole, SysMenu
from app.models.microservice import SysMicroservice
from app.models.log import SysLoginLog
from app.schemas.common import Result
from app.schemas.auth import (
    LoginRequest, RegisterRequest, UpdateProfileRequest,
    ChangePasswordRequest, TokenResponse, UserInfoResponse,
    MyAppItem
)

router = APIRouter(prefix="/auth", tags=["01.认证与身份中心"])

@router.post("/register", response_model=Result[TokenResponse], summary="用户注册")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    # 检查用户名是否已存在
    existing = db.query(SysUser).filter(SysUser.username == req.username, SysUser.is_deleted == 0).first()
    if existing:
        return Result.fail(f"用户名 '{req.username}' 已被占用，请更换", code=400)

    # 默认分配操作员/探索者角色
    default_role = db.query(SysRole).filter(SysRole.role_code == "ROLE_OPERATOR").first()
    
    new_user = SysUser(
        username=req.username,
        password_hash=get_password_hash(req.password),
        real_name=req.real_name or req.username,
        email=req.email,
        avatar=req.avatar or f"https://api.dicebear.com/7.x/bottts/svg?seed={req.username}",
        is_superadmin=0,
        tenant_code="SYSTEM",
        status="ACTIVE",
        remark="自主注册用户"
    )
    if default_role:
        new_user.roles.append(default_role)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 生成 Token
    role_codes = [r.role_code for r in new_user.roles]
    extra_data = {
        "user_id": new_user.id,
        "is_superadmin": False,
        "roles": role_codes
    }
    access_token = create_access_token(subject=new_user.username, extra_data=extra_data)

    user_info = UserInfoResponse(
        id=new_user.id,
        username=new_user.username,
        real_name=new_user.real_name,
        email=new_user.email,
        phone=new_user.phone,
        avatar=new_user.avatar,
        personality_color=req.personality_color or "BLUE",
        zodiac=req.zodiac or "天秤座",
        unlocked_data=None,
        is_superadmin=False,
        roles=role_codes,
        permissions=[]
    )

    token_resp = TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_info=user_info
    )
    return Result.ok(data=token_resp, message="注册成功，欢迎开启应用平台！")

@router.post("/login", response_model=Result[TokenResponse], summary="用户与管理员登录")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(SysUser).filter(
        SysUser.username == req.username,
        SysUser.is_deleted == 0
    ).first()

    if not user or not verify_password(req.password, user.password_hash):
        db.add(SysLoginLog(username=req.username, status="FAIL", msg="用户名或密码错误"))
        db.commit()
        return Result.fail("用户名或密码错误", code=400)

    if user.status != "ACTIVE":
        db.add(SysLoginLog(username=req.username, status="FAIL", msg="账号已被停用"))
        db.commit()
        return Result.fail("该账号已被管理员停用，请联系超级管理员", code=403)

    # 收集角色与权限
    role_codes = [r.role_code for r in user.roles if r.status == "ACTIVE"]
    permissions = []
    for r in user.roles:
        for m in r.menus:
            if m.permission and m.is_visible:
                permissions.append(m.permission)

    # 生成 Token 载荷
    extra_data = {
        "user_id": user.id,
        "is_superadmin": bool(user.is_superadmin),
        "roles": role_codes
    }
    access_token = create_access_token(subject=user.username, extra_data=extra_data)

    user_info = UserInfoResponse(
        id=user.id,
        username=user.username,
        real_name=user.real_name,
        email=user.email,
        phone=user.phone,
        avatar=user.avatar,
        personality_color="BLUE",
        zodiac=None,
        unlocked_data=None,
        is_superadmin=bool(user.is_superadmin),
        roles=role_codes,
        permissions=list(set(permissions))
    )

    db.add(SysLoginLog(username=user.username, status="SUCCESS", msg="登录成功"))
    db.commit()

    token_resp = TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_info=user_info
    )
    return Result.ok(data=token_resp, message="登录成功")

@router.get("/me", response_model=Result[UserInfoResponse], summary="获取当前登录用户信息与画像")
def get_current_user_info(payload: dict = Depends(get_current_user_payload), db: Session = Depends(get_db)):
    username = payload.get("sub")
    user = db.query(SysUser).filter(SysUser.username == username, SysUser.is_deleted == 0).first()
    if not user:
        return Result.fail("用户不存在", code=404)

    role_codes = [r.role_code for r in user.roles if r.status == "ACTIVE"]
    permissions = []
    for r in user.roles:
        for m in r.menus:
            if m.permission:
                permissions.append(m.permission)

    user_info = UserInfoResponse(
        id=user.id,
        username=user.username,
        real_name=user.real_name,
        email=user.email,
        phone=user.phone,
        avatar=user.avatar,
        personality_color="BLUE",
        zodiac=None,
        unlocked_data=None,
        is_superadmin=bool(user.is_superadmin),
        roles=role_codes,
        permissions=list(set(permissions))
    )
    return Result.ok(data=user_info)

@router.put("/profile", response_model=Result[UserInfoResponse], summary="更新用户基本资料")
def update_profile(req: UpdateProfileRequest, payload: dict = Depends(get_current_user_payload), db: Session = Depends(get_db)):
    username = payload.get("sub")
    user = db.query(SysUser).filter(SysUser.username == username, SysUser.is_deleted == 0).first()
    if not user:
        return Result.fail("用户不存在", code=404)

    if req.real_name is not None:
        user.real_name = req.real_name
    if req.email is not None:
        user.email = req.email
    if req.avatar is not None:
        user.avatar = req.avatar

    db.commit()
    db.refresh(user)

    role_codes = [r.role_code for r in user.roles if r.status == "ACTIVE"]
    user_info = UserInfoResponse(
        id=user.id,
        username=user.username,
        real_name=user.real_name,
        email=user.email,
        phone=user.phone,
        avatar=user.avatar,
        personality_color="BLUE",
        zodiac=None,
        unlocked_data=None,
        is_superadmin=bool(user.is_superadmin),
        roles=role_codes,
        permissions=[]
    )
    return Result.ok(data=user_info, message="个人资料更新成功")
    
@router.post("/change-password", response_model=Result[bool], summary="修改当前用户密码")
def change_password(req: ChangePasswordRequest, payload: dict = Depends(get_current_user_payload), db: Session = Depends(get_db)):
    username = payload.get("sub")
    user = db.query(SysUser).filter(SysUser.username == username, SysUser.is_deleted == 0).first()
    if not user:
        return Result.fail("用户不存在", code=404)

    if not verify_password(req.old_password, user.password_hash):
        return Result.fail("原密码不正确，请重新输入", code=400)

    if len(req.new_password) < 6:
        return Result.fail("新密码长度不能少于 6 位", code=400)

    user.password_hash = get_password_hash(req.new_password)
    db.commit()
    return Result.ok(data=True, message="密码修改成功，请使用新密码重新登录")

@router.get("/my-apps", response_model=Result[List[MyAppItem]], summary="获取当前登录用户已授权的微服务应用与工具清单")
def get_my_permitted_apps(
    payload: Optional[dict] = Depends(get_optional_user_payload),
    db: Session = Depends(get_db)
):
    """
    根据当前登录用户（及所属角色分配的微服务权限）动态返回已授权的应用清单。
    - 超级管理员：拥有所有已注册微服务与基座治理工具
    - 赋予了特定微服务的角色：按角色权限展示对应应用节点
    - 未登录访客：展示默认公开业务应用（角色宇宙等）
    """
    is_superadmin = False
    allowed_service_codes = set()
    user = None

    if payload:
        username = payload.get("sub")
        if username:
            user = db.query(SysUser).filter(SysUser.username == username, SysUser.is_deleted == 0).first()
            if user:
                if user.is_superadmin or user.username == settings.SUPERADMIN_USERNAME:
                    is_superadmin = True
                else:
                    for r in user.roles:
                        if r.status == "ACTIVE" and r.is_deleted == 0:
                            for m in r.menus:
                                if m.service_code and m.is_deleted == 0:
                                    allowed_service_codes.add(m.service_code)

    # 查出当前平台所有已登记生效的微服务
    registered_svcs = db.query(SysMicroservice).filter(
        SysMicroservice.is_deleted == 0,
        SysMicroservice.status == "ACTIVE"
    ).all()
    svc_map = {s.service_code: s for s in registered_svcs}

    apps: List[MyAppItem] = []

    # 1. 角色宇宙与主站业务 (mcp-service-universe)
    # 规则：公开可见，或者用户拥有 mcp-service-universe 权限 / 超管
    if is_superadmin or "mcp-service-universe" in allowed_service_codes or payload is None or len(allowed_service_codes) == 0:
        universe_svc = svc_map.get("mcp-service-universe")
        apps.append(MyAppItem(
            id="app-universe",
            service_code="mcp-service-universe",
            name="角色宇宙",
            sub="DreamClip Universe",
            icon="🌌",
            gradient="linear-gradient(135deg, #4f46e5, #06b6d4)",
            url="/universe",
            category="BIZ",
            badge="主站",
            is_admin=False,
            description="沉浸式角色互动与原创深度文学元宇宙",
            health_status=universe_svc.health_status if universe_svc else "HEALTHY"
        ))
        apps.append(MyAppItem(
            id="app-capsules",
            service_code="mcp-service-universe",
            name="情绪胶囊",
            sub="Emotion Lab",
            icon="💊",
            gradient="linear-gradient(135deg, #0ea5e9, #6366f1)",
            url="/universe#capsules-section",
            category="BIZ",
            badge="文学",
            is_admin=False,
            description="打捞星穹深处每一粒情绪胶囊",
            health_status=universe_svc.health_status if universe_svc else "HEALTHY"
        ))
        apps.append(MyAppItem(
            id="app-theatre",
            service_code="mcp-service-universe",
            name="AVG 沉浸剧场",
            sub="DreamClip Theatre",
            icon="🎮",
            gradient="linear-gradient(135deg, #8b5cf6, #ec4899)",
            url="/games",
            category="GAME",
            badge="互动",
            is_admin=False,
            description="原创 AVG 分支沉浸剧场与互动体验",
            health_status=universe_svc.health_status if universe_svc else "HEALTHY"
        ))

    # 2. 开发者 API 开放文档 (公开可见)
    apps.append(MyAppItem(
        id="app-docs",
        service_code="mcp-base",
        name="API 开放文档",
        sub="OpenAPI Swagger",
        icon="📖",
        gradient="linear-gradient(135deg, #10b981, #059669)",
        url="/base/docs",
        category="TOOL",
        badge="接口",
        is_admin=False,
        description="微服务架构 OpenAPI 3.0 标准接口在线调试中心",
        health_status="HEALTHY"
    ))

    # 3. 登录用户专属资产应用
    if user:
        apps.append(MyAppItem(
            id="app-vault",
            service_code="mcp-service-universe",
            name="星际背包",
            sub="Capsule Vault",
            icon="🎒",
            gradient="linear-gradient(135deg, #f59e0b, #d97706)",
            url="/universe",
            category="BIZ",
            badge="资产",
            is_admin=False,
            description="用户个性化情绪胶囊与个人星际档案背包",
            health_status="HEALTHY"
        ))

    # 4. 平台治理底座应用 (仅当拥有 mcp-base 权限或超管时展现)
    if is_superadmin or "mcp-base" in allowed_service_codes:
        base_svc = svc_map.get("mcp-base")
        base_health = base_svc.health_status if base_svc else "HEALTHY"
        
        apps.append(MyAppItem(
            id="app-base",
            service_code="mcp-base",
            name="MCP Base 控制台",
            sub="底座运维与微服务治理",
            icon="⭐",
            gradient="linear-gradient(135deg, #6366f1, #3b82f6)",
            url="https://base.dreamclip.cn/",
            category="BASE",
            badge="底座",
            is_admin=True,
            description="微服务注册生命周期、健康探活巡检与技术底座管理",
            health_status=base_health
        ))
        apps.append(MyAppItem(
            id="app-users",
            service_code="mcp-base",
            name="用户与角色权限中心",
            sub="平台用户与微服务赋权",
            icon="👥",
            gradient="linear-gradient(135deg, #8b5cf6, #a855f7)",
            url="https://base.dreamclip.cn/?tab=tab-users",
            category="BASE",
            badge="IAM",
            is_admin=True,
            description="平台用户密码修改、角色创建与微服务清单授权管理",
            health_status=base_health
        ))
        apps.append(MyAppItem(
            id="app-configs",
            service_code="mcp-base",
            name="全局参数字典",
            sub="系统运行参数与字典",
            icon="⚙️",
            gradient="linear-gradient(135deg, #64748b, #475569)",
            url="https://base.dreamclip.cn/?tab=tab-configs",
            category="BASE",
            badge="配置",
            is_admin=True,
            description="系统级参数热更新与微服务数据字典配置中心",
            health_status=base_health
        ))

    # 5. 动态挂载其他第三方/扩展已注册微服务 (如有)
    for svc in registered_svcs:
        if svc.service_code in ["mcp-base", "mcp-portal", "mcp-service-universe"]:
            continue
        if is_superadmin or svc.service_code in allowed_service_codes:
            apps.append(MyAppItem(
                id=f"app-custom-{svc.service_code}",
                service_code=svc.service_code,
                name=svc.service_name,
                sub=svc.service_code,
                icon="🔌",
                gradient="linear-gradient(135deg, #3b82f6, #8b5cf6)",
                url=svc.gateway_prefix or svc.base_url,
                category=svc.category or "BIZ",
                badge=svc.tech_stack or "SVC",
                is_admin=svc.category == "BASE",
                description=svc.description or "已接入平台的独立微服务",
                health_status=svc.health_status or "HEALTHY"
            ))

    return Result.ok(data=apps)
