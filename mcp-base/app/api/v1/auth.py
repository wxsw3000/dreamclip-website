from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token, get_current_user_payload
from app.models.user import SysUser, SysRole
from app.models.log import SysLoginLog
from app.schemas.common import Result
from app.schemas.auth import LoginRequest, RegisterRequest, UpdateProfileRequest, ChangePasswordRequest, TokenResponse, UserInfoResponse

router = APIRouter(prefix="/auth", tags=["01.认证与身份中心"])

@router.post("/register", response_model=Result[TokenResponse], summary="用户注册 (带性格色彩与星座画像)")
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
        personality_color=req.personality_color or "BLUE",
        zodiac=req.zodiac or "天秤座",
        avatar=req.avatar or f"https://api.dicebear.com/7.x/bottts/svg?seed={req.username}",
        is_superadmin=0,
        tenant_code="SYSTEM",
        status="ACTIVE",
        remark="自主注册探索者"
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
        personality_color=new_user.personality_color,
        zodiac=new_user.zodiac,
        unlocked_data=new_user.unlocked_data,
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
    return Result.ok(data=token_resp, message="注册成功，欢迎开启 DreamClip 角色宇宙！")

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
        personality_color=user.personality_color or "BLUE",
        zodiac=user.zodiac,
        unlocked_data=user.unlocked_data,
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
        personality_color=user.personality_color or "BLUE",
        zodiac=user.zodiac,
        unlocked_data=user.unlocked_data,
        is_superadmin=bool(user.is_superadmin),
        roles=role_codes,
        permissions=list(set(permissions))
    )
    return Result.ok(data=user_info)

@router.put("/profile", response_model=Result[UserInfoResponse], summary="更新用户画像与资料")
def update_profile(req: UpdateProfileRequest, payload: dict = Depends(get_current_user_payload), db: Session = Depends(get_db)):
    username = payload.get("sub")
    user = db.query(SysUser).filter(SysUser.username == username, SysUser.is_deleted == 0).first()
    if not user:
        return Result.fail("用户不存在", code=404)

    if req.real_name is not None:
        user.real_name = req.real_name
    if req.email is not None:
        user.email = req.email
    if req.personality_color is not None:
        user.personality_color = req.personality_color
    if req.zodiac is not None:
        user.zodiac = req.zodiac
    if req.avatar is not None:
        user.avatar = req.avatar
    if req.unlocked_data is not None:
        user.unlocked_data = req.unlocked_data

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
        personality_color=user.personality_color or "BLUE",
        zodiac=user.zodiac,
        unlocked_data=user.unlocked_data,
        is_superadmin=bool(user.is_superadmin),
        roles=role_codes,
        permissions=[]
    )
    return Result.ok(data=user_info, message="资料与画像更新成功")
    
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

