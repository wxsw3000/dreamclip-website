from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.security import get_current_superadmin, get_password_hash
from app.models.user import SysUser, SysRole, SysMenu
from app.schemas.common import Result, PageResult
from app.schemas.user import UserCreate, UserUpdate, UserOut, RoleOut, RoleCreate, RoleUpdate, RoleAssignPermissions, MenuOut

router = APIRouter(prefix="/system", tags=["05.用户权限与菜单管理"])

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

    user_dict = req.model_dump(exclude={"password"})
    user_dict["password_hash"] = get_password_hash(req.password)
    new_user = SysUser(**user_dict)
    
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

# ---------- 角色与应用权限管理 ----------

@router.get("/roles", response_model=Result[List[RoleOut]], summary="获取系统角色列表")
def list_roles(db: Session = Depends(get_db)):
    roles = db.query(SysRole).filter(SysRole.is_deleted == 0).order_by(SysRole.role_level.asc()).all()
    return Result.ok(data=roles)

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
    if req.menu_ids:
        menus = db.query(SysMenu).filter(SysMenu.id.in_(req.menu_ids), SysMenu.is_deleted == 0).all()
        new_role.menus = menus

    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return Result.ok(data=new_role, message="角色创建成功")

@router.put("/roles/{role_id}", response_model=Result[RoleOut], summary="修改角色信息")
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
    if "menu_ids" in update_data:
        menu_ids = update_data.pop("menu_ids")
        if menu_ids is not None:
            menus = db.query(SysMenu).filter(SysMenu.id.in_(menu_ids), SysMenu.is_deleted == 0).all()
            role.menus = menus

    for k, v in update_data.items():
        setattr(role, k, v)

    db.commit()
    db.refresh(role)
    return Result.ok(data=role, message="角色修改成功")

@router.delete("/roles/{role_id}", response_model=Result[bool], summary="删除角色")
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_superadmin)
):
    role = db.query(SysRole).filter(SysRole.id == role_id, SysRole.is_deleted == 0).first()
    if not role:
        return Result.fail("角色不存在", code=404)
    if role.role_code in ["ROLE_SUPERADMIN", "ROLE_OPERATOR"]:
        return Result.fail(f"系统内置角色 {role.role_code} 不允许删除", code=400)

    role.is_deleted = 1
    db.commit()
    return Result.ok(data=True, message="角色已删除")

@router.put("/roles/{role_id}/permissions", response_model=Result[bool], summary="给角色赋予应用/菜单权限")
def assign_role_permissions(
    role_id: int,
    req: RoleAssignPermissions,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_superadmin)
):
    role = db.query(SysRole).filter(SysRole.id == role_id, SysRole.is_deleted == 0).first()
    if not role:
        return Result.fail("角色不存在", code=404)

    menus = db.query(SysMenu).filter(SysMenu.id.in_(req.menu_ids), SysMenu.is_deleted == 0).all()
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

