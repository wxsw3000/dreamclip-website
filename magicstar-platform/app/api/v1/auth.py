import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
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

logger = logging.getLogger("mcp-base.auth")
router = APIRouter(prefix="/auth", tags=["01.认证与身份中心"])

@router.post("/register", response_model=Result[TokenResponse], summary="用户注册")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    try:
        clean_username = req.username.strip()
        if len(clean_username) < 3 or len(clean_username) > 32:
            return Result.fail("用户名长度需在 3 到 32 个字符之间", code=400)

        # 1. 检查用户名是否存在（全量检索）
        existing = db.query(SysUser).filter(SysUser.username == clean_username).first()

        # 2. 检查电子邮箱唯一性 (若填写了邮箱)
        if req.email and req.email.strip():
            clean_email = req.email.strip()
            existing_email = db.query(SysUser).filter(SysUser.email == clean_email, SysUser.is_deleted == 0).first()
            if existing_email and (not existing or existing_email.id != existing.id):
                return Result.fail(f"电子邮箱 '{clean_email}' 已被其他账号使用，请更换邮箱", code=400)
        else:
            clean_email = None

        # 默认分配平台标准注册会员角色 (ROLE_MEMBER)
        default_role = db.query(SysRole).filter(SysRole.role_code == "ROLE_MEMBER", SysRole.is_deleted == 0).first()
        if not default_role:
            default_role = db.query(SysRole).filter(SysRole.role_code == "ROLE_OPERATOR", SysRole.is_deleted == 0).first()

        if existing:
            if existing.is_deleted == 0:
                return Result.fail(f"用户名 '{clean_username}' 已被注册占用，请直接登录或更换用户名", code=400)
            else:
                # 若此前处于已删除状态，重置激活该账号并更新资料
                existing.is_deleted = 0
                existing.password_hash = get_password_hash(req.password)
                existing.real_name = req.real_name or clean_username
                existing.email = clean_email
                existing.avatar = req.avatar or f"https://api.dicebear.com/7.x/bottts/svg?seed={clean_username}"
                existing.status = "ACTIVE"
                existing.remark = "自主重新注册激活"
                if default_role and default_role not in existing.roles:
                    existing.roles.append(default_role)
                db.commit()
                db.refresh(existing)
                new_user = existing
        else:
            new_user = SysUser(
                username=clean_username,
                password_hash=get_password_hash(req.password),
                real_name=req.real_name or clean_username,
                email=clean_email,
                avatar=req.avatar or f"https://api.dicebear.com/7.x/bottts/svg?seed={clean_username}",
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
        role_codes = [r.role_code for r in new_user.roles] if new_user.roles else ["ROLE_MEMBER"]
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
        logger.info("User registered successfully: %s (ID: %s, Role: %s)", new_user.username, new_user.id, role_codes)
        return Result.ok(data=token_resp, message="注册成功，欢迎开启应用平台！")
    except IntegrityError as ie:
        db.rollback()
        logger.warning("Integrity error on register for %s: %s", req.username, ie)
        return Result.fail(f"用户名 '{req.username}' 已被占用，请直接登录或更换用户名", code=400)
    except Exception as e:
        db.rollback()
        logger.error("User registration error for %s: %s", req.username, e, exc_info=True)
        return Result.fail(f"注册处理失败: {str(e)}", code=500)

@router.post("/login", response_model=Result[TokenResponse], summary="用户与管理员登录")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(SysUser).filter(
            SysUser.username == req.username,
            SysUser.is_deleted == 0
        ).first()

        if not user or not verify_password(req.password, user.password_hash):
            try:
                db.add(SysLoginLog(username=req.username, status="FAIL", msg="用户名或密码错误"))
                db.commit()
            except Exception:
                db.rollback()
            return Result.fail("用户名或密码错误", code=400)

        if user.status != "ACTIVE":
            try:
                db.add(SysLoginLog(username=req.username, status="FAIL", msg="账号已被停用"))
                db.commit()
            except Exception:
                db.rollback()
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

        try:
            db.add(SysLoginLog(username=user.username, status="SUCCESS", msg="登录成功"))
            db.commit()
        except Exception:
            db.rollback()

        token_resp = TokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_info=user_info
        )
        return Result.ok(data=token_resp, message="登录成功")
    except Exception as e:
        db.rollback()
        logger.error("Login error for %s: %s", req.username, e, exc_info=True)
        return Result.fail(f"登录处理失败: {str(e)}", code=500)

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

    # 查出当前平台所有已登记生效的微服务 (sys_microservice 表)
    registered_svcs = db.query(SysMicroservice).filter(
        SysMicroservice.is_deleted == 0,
        SysMicroservice.status == "ACTIVE"
    ).order_by(SysMicroservice.id.asc()).all()

    # 应用图标与渐变映射
    icon_map = {
        "magicstar-platform": "⭐",
        "dreamclip": "🌌",
        "mcp-base": "⭐",
        "mcp-service-universe": "🌌",
        "mcp-service-game": "🎮",
        "mcp-service-mdm": "🏭",
        "mcp-service-ai": "🤖",
        "mcp-service-data": "💾"
    }

    gradient_map = {
        "magicstar-platform": "linear-gradient(135deg, #6366f1, #3b82f6)",
        "dreamclip": "linear-gradient(135deg, #4f46e5, #06b6d4)",
        "mcp-base": "linear-gradient(135deg, #6366f1, #3b82f6)",
        "mcp-service-universe": "linear-gradient(135deg, #4f46e5, #06b6d4)",
        "mcp-service-game": "linear-gradient(135deg, #8b5cf6, #ec4899)",
        "mcp-service-ai": "linear-gradient(135deg, #10b981, #059669)",
        "mcp-service-mdm": "linear-gradient(135deg, #f59e0b, #d97706)"
    }

    apps: List[MyAppItem] = []

    # 核心设计原则：一个微服务就是一个独立应用 (1 Microservice = 1 Application)
    for svc in registered_svcs:
        is_base_app = (svc.category == "BASE" or svc.service_code in ["magicstar-platform", "mcp-base"])

        # 权限校验：
        # 1. 超级管理员：天生拥有全量应用权限
        # 2. 登录用户：严格取决于该用户所属角色是否具有该应用的权限 (service_code in allowed_service_codes)
        # 3. 未登录访客：展示默认公开业务应用
        if is_superadmin:
            has_permission = True
        elif user is not None:
            has_permission = (svc.service_code in allowed_service_codes or is_base_app and user.is_superadmin)
        else:
            # 未登录访客
            has_permission = (not is_base_app)

        if not has_permission:
            continue

        # 确定应用启动入口 URL
        if svc.service_code in ["magicstar-platform", "mcp-base"]:
            app_url = "/admin"
        elif svc.service_code in ["dreamclip", "mcp-service-universe"]:
            app_url = "http://127.0.0.1:8081/"
        else:
            app_url = svc.gateway_prefix or svc.base_url

        apps.append(MyAppItem(
            id=f"app-{svc.service_code}",
            service_code=svc.service_code,
            name=svc.service_name,
            sub=svc.service_code,
            icon=icon_map.get(svc.service_code, "🔌"),
            gradient=gradient_map.get(svc.service_code, "linear-gradient(135deg, #3b82f6, #8b5cf6)"),
            url=app_url,
            category=svc.category or ("BASE" if is_base_app else "BIZ"),
            badge=svc.tech_stack or ("BASE" if is_base_app else "APP"),
            is_admin=is_base_app,
            description=svc.description or f"已接入平台的独立微服务应用 ({svc.service_name})",
            health_status=svc.health_status or "HEALTHY"
        ))

    return Result.ok(data=apps)
