from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.security import get_current_superadmin, get_password_hash
from app.models.user import SysUser, SysRole, SysMenu
from app.models.microservice import SysMicroservice
from app.schemas.common import Result, PageResult
from app.schemas.user import (
    UserCreate, UserUpdate, UserOut,
    RoleOut, RoleCreate, RoleUpdate, RoleAssignPermissions, RolePermissionOut,
    AppPermissionItem, MenuSimple, MenuOut
)

router = APIRouter(prefix="/system", tags=["05.用户权限与微服务应用授权"])

# ---------- 用户管理 ----------

@router.get("/users", response_model=Result[PageResult[UserOut]], summary="分页查询平台用户")
def list_users(
    current: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    keyword: Optional[str] = None,
    tenant_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(SysUser).filter(SysUser.is_deleted == 0)
    if keyword:
        query = query.filter(
            (SysUser.username.ilike(f"%{keyword}%")) |
            (SysUser.real_name.ilike(f"%{keyword}%"))
        )
    if tenant_code:
        query = query.filter(SysUser.tenant_code == tenant_code)

    total = query.count()
    records = query.order_by(desc(SysUser.id)).offset((current - 1) * size).limit(size).all()
    
    return Result.ok(data=PageResult(
        total=total,
        current=current,
        size=size,
        records=records
    ))

@router.post("/users", response_model=Result[UserOut], summary="新增平台用户")
def create_user(
    req: UserCreate,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_superadmin)
):
    existing = db.query(SysUser).filter(SysUser.username == req.username, SysUser.is_deleted == 0).first()
    if existing:
        return Result.fail(f"用户名 {req.username} 已存在", code=400)

    user_dict = req.model_dump(exclude={"password", "role_ids"})
    user_dict["password_hash"] = get_password_hash(req.password)
    new_user = SysUser(**user_dict)
    
    if req.role_ids:
        roles = db.query(SysRole).filter(SysRole.id.in_(req.role_ids), SysRole.is_deleted == 0).all()
        new_user.roles = roles
    else:
        # 默认分配操作员角色
        default_role = db.query(SysRole).filter(SysRole.role_code == "ROLE_OPERATOR", SysRole.is_deleted == 0).first()
        if default_role:
            new_user.roles.append(default_role)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return Result.ok(data=new_user, message="用户创建成功")

@router.put("/users/{user_id}", response_model=Result[UserOut], summary="修改用户信息与重置密码")
def update_user(
    user_id: int,
    req: UserUpdate,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_superadmin)
):
    user = db.query(SysUser).filter(SysUser.id == user_id, SysUser.is_deleted == 0).first()
    if not user:
        return Result.fail("用户不存在", code=404)

    update_data = req.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        user.password_hash = get_password_hash(update_data.pop("password"))

    if "role_ids" in update_data:
        role_ids = update_data.pop("role_ids")
        if role_ids is not None:
            roles = db.query(SysRole).filter(SysRole.id.in_(role_ids), SysRole.is_deleted == 0).all()
            user.roles = roles

    for k, v in update_data.items():
        setattr(user, k, v)

    db.commit()
    db.refresh(user)
    return Result.ok(data=user, message="用户信息与密码已成功更新")

@router.delete("/users/{user_id}", response_model=Result[bool], summary="删除用户")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_superadmin)
):
    user = db.query(SysUser).filter(SysUser.id == user_id, SysUser.is_deleted == 0).first()
    if not user:
        return Result.fail("用户不存在", code=404)
    if user.username == "superadmin":
        return Result.fail("不允许删除超级管理员 superadmin", code=400)

    user.is_deleted = 1
    db.commit()
    return Result.ok(data=True, message="用户已删除")

# ---------- 角色与微服务应用权限管理 ----------

@router.get("/roles/assignable-apps", response_model=Result[List[AppPermissionItem]], summary="获取可供角色勾选授权的平台应用清单")
def get_assignable_apps(db: Session = Depends(get_db)):
    """返回全量已注册微服务应用及其功能点，供管理员按应用清单直观勾选"""
    services = db.query(SysMicroservice).filter(SysMicroservice.is_deleted == 0, SysMicroservice.status == "ACTIVE").all()
    all_menus = db.query(SysMenu).filter(SysMenu.is_deleted == 0, SysMenu.is_visible == 1).all()
    
    icon_map = {
        "mcp-base": "⭐",
        "mcp-portal": "📱",
        "mcp-service-universe": "🌌",
        "mcp-service-mdm": "🏭",
        "mcp-service-data": "💾",
        "mcp-service-qa": "🤖"
    }

    app_items = []
    for s in services:
        svc_menus = [MenuSimple.model_validate(m) for m in all_menus if m.service_code == s.service_code and m.menu_type != "APP"]
        
        # 确保该微服务自身在 sys_menu 表中有统一的 APP 类型权限节点
        app_menu = db.query(SysMenu).filter(
            SysMenu.service_code == s.service_code,
            SysMenu.menu_type == "APP",
            SysMenu.is_deleted == 0
        ).first()
        
        if not app_menu:
            app_menu = SysMenu(
                parent_id=0,
                menu_name=s.service_name,
                menu_type="APP",
                path=s.gateway_prefix or s.base_url,
                icon=icon_map.get(s.service_code, "🔌"),
                service_code=s.service_code,
                sort_order=s.id,
                is_visible=1
            )
            db.add(app_menu)
            db.commit()
            db.refresh(app_menu)

        app_items.append(AppPermissionItem(
            id=app_menu.id,
            service_code=s.service_code,
            service_name=s.service_name,
            category=s.category or "BIZ",
            tech_stack=s.tech_stack or "PYTHON",
            base_url=s.base_url,
            gateway_prefix=s.gateway_prefix or "",
            icon=icon_map.get(s.service_code, "🔌"),
            description=s.description or "运行于平台的独立微服务节点",
            health_status=s.health_status or "HEALTHY",
            menus=svc_menus
        ))

    return Result.ok(data=app_items)

@router.get("/roles", response_model=Result[List[RoleOut]], summary="获取系统角色列表 (包含赋予的应用)")
def list_roles(db: Session = Depends(get_db)):
    roles = db.query(SysRole).filter(SysRole.is_deleted == 0).order_by(SysRole.role_level.asc()).all()
    role_outs = []
    for r in roles:
        # 提取已赋权的应用名称清单
        assigned_apps = []
        for m in r.menus:
            if m.menu_name and m.menu_name not in assigned_apps:
                assigned_apps.append(m.menu_name)

        role_outs.append(RoleOut(
            id=r.id,
            role_code=r.role_code,
            role_name=r.role_name,
            role_level=r.role_level,
            status=r.status,
            remark=r.remark,
            created_at=r.created_at,
            assigned_apps=assigned_apps,
            menus=[MenuSimple.model_validate(m) for m in r.menus if m.is_deleted == 0]
        ))
    return Result.ok(data=role_outs)

@router.get("/roles/{role_id}/permissions", response_model=Result[RolePermissionOut], summary="获取指定角色的应用与功能权限详情")
def get_role_permissions(role_id: int, db: Session = Depends(get_db)):
    role = db.query(SysRole).filter(SysRole.id == role_id, SysRole.is_deleted == 0).first()
    if not role:
        return Result.fail("角色不存在", code=404)

    assigned_menu_ids = [m.id for m in role.menus if m.is_deleted == 0]
    assigned_service_codes = list(set([m.service_code for m in role.menus if m.service_code and m.is_deleted == 0]))

    apps_res = get_assignable_apps(db)
    all_apps = apps_res.data or []

    return Result.ok(data=RolePermissionOut(
        role_id=role.id,
        role_code=role.role_code,
        role_name=role.role_name,
        assigned_service_codes=assigned_service_codes,
        assigned_menu_ids=assigned_menu_ids,
        all_apps=all_apps
    ))

@router.post("/roles", response_model=Result[RoleOut], summary="创建平台角色")
def create_role(
    req: RoleCreate,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_superadmin)
):
    existing = db.query(SysRole).filter(SysRole.role_code == req.role_code, SysRole.is_deleted == 0).first()
    if existing:
        return Result.fail(f"角色编码 '{req.role_code}' 已存在", code=400)

    new_role = SysRole(
        role_code=req.role_code,
        role_name=req.role_name,
        role_level=req.role_level,
        status=req.status,
        remark=req.remark
    )
    
    selected_menu_ids = set(req.menu_ids or [])
    if req.service_codes:
        app_menus = db.query(SysMenu).filter(
            SysMenu.service_code.in_(req.service_codes),
            SysMenu.menu_type == "APP",
            SysMenu.is_deleted == 0
        ).all()
        for am in app_menus:
            selected_menu_ids.add(am.id)

    if selected_menu_ids:
        menus = db.query(SysMenu).filter(SysMenu.id.in_(list(selected_menu_ids)), SysMenu.is_deleted == 0).all()
        new_role.menus = menus

    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    
    assigned_apps = [m.menu_name for m in new_role.menus]
    return Result.ok(data=RoleOut(
        id=new_role.id,
        role_code=new_role.role_code,
        role_name=new_role.role_name,
        role_level=new_role.role_level,
        status=new_role.status,
        remark=new_role.remark,
        created_at=new_role.created_at,
        assigned_apps=assigned_apps,
        menus=[MenuSimple.model_validate(m) for m in new_role.menus]
    ), message="角色创建成功")

@router.put("/roles/{role_id}", response_model=Result[RoleOut], summary="修改角色基础信息")
def update_role(
    role_id: int,
    req: RoleUpdate,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_superadmin)
):
    role = db.query(SysRole).filter(SysRole.id == role_id, SysRole.is_deleted == 0).first()
    if not role:
        return Result.fail("角色不存在", code=404)

    update_data = req.model_dump(exclude_unset=True)
    update_data.pop("service_codes", None)
    update_data.pop("menu_ids", None)

    for k, v in update_data.items():
        setattr(role, k, v)

    db.commit()
    db.refresh(role)
    
    assigned_apps = [m.menu_name for m in role.menus]
    return Result.ok(data=RoleOut(
        id=role.id,
        role_code=role.role_code,
        role_name=role.role_name,
        role_level=role.role_level,
        status=role.status,
        remark=role.remark,
        created_at=role.created_at,
        assigned_apps=assigned_apps,
        menus=[MenuSimple.model_validate(m) for m in role.menus]
    ), message="角色修改成功")

@router.delete("/roles/{role_id}", response_model=Result[bool], summary="删除角色")
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_superadmin)
):
    role = db.query(SysRole).filter(SysRole.id == role_id, SysRole.is_deleted == 0).first()
    if not role:
        return Result.fail("角色不存在", code=404)
    if role.role_code in ["ROLE_SUPER_ADMIN", "ROLE_SUPERADMIN", "ROLE_OPERATOR"]:
        return Result.fail(f"系统内置角色 {role.role_code} 不允许删除", code=400)

    role.is_deleted = 1
    db.commit()
    return Result.ok(data=True, message="角色已删除")

@router.put("/roles/{role_id}/permissions", response_model=Result[bool], summary="为角色赋予应用清单与菜单权限")
def assign_role_permissions(
    role_id: int,
    req: RoleAssignPermissions,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_superadmin)
):
    role = db.query(SysRole).filter(SysRole.id == role_id, SysRole.is_deleted == 0).first()
    if not role:
        return Result.fail("角色不存在", code=404)

    all_selected_menu_ids = set(req.menu_ids or [])
    
    # 自动关联所勾选微服务对应的应用权限点
    if req.service_codes:
        app_menus = db.query(SysMenu).filter(
            SysMenu.service_code.in_(req.service_codes),
            SysMenu.menu_type == "APP",
            SysMenu.is_deleted == 0
        ).all()
        for am in app_menus:
            all_selected_menu_ids.add(am.id)

    menus = db.query(SysMenu).filter(SysMenu.id.in_(list(all_selected_menu_ids)), SysMenu.is_deleted == 0).all()
    role.menus = menus
    db.commit()
    return Result.ok(data=True, message="角色应用权限配置成功")

# ---------- 菜单与动态路由树 ----------

@router.get("/menus/flat", response_model=Result[List[MenuOut]], summary="获取扁平全量菜单与应用权限列表")
def get_flat_menus(db: Session = Depends(get_db)):
    all_menus = db.query(SysMenu).filter(
        SysMenu.is_deleted == 0,
        SysMenu.is_visible == 1
    ).order_by(SysMenu.sort_order.asc()).all()
    return Result.ok(data=all_menus)

@router.get("/menus/tree", response_model=Result[List[MenuOut]], summary="获取全量菜单树")
def get_menu_tree(db: Session = Depends(get_db)):
    all_menus = db.query(SysMenu).filter(
        SysMenu.is_deleted == 0,
        SysMenu.is_visible == 1
    ).order_by(SysMenu.sort_order.asc()).all()

    menu_map = {m.id: MenuOut.model_validate(m) for m in all_menus}
    root_menus = []
    
    for m in all_menus:
        menu_dto = menu_map[m.id]
        if m.parent_id == 0 or m.parent_id not in menu_map:
            root_menus.append(menu_dto)
        else:
            parent_dto = menu_map[m.parent_id]
            parent_dto.children.append(menu_dto)

    return Result.ok(data=root_menus)
