from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.security import get_current_superadmin, get_password_hash
from app.models.user import SysUser, SysRole, SysMenu
from app.schemas.common import Result, PageResult
from app.schemas.user import UserCreate, UserUpdate, UserOut, RoleOut, RoleCreate, MenuOut

router = APIRouter(prefix="/system", tags=["05.用户权限与菜单管理"])

# ---------- 用户管理 ----------

@router.get("/users", response_model=Result[PageResult[UserOut]], summary="分页查询平台用户")
def list_users(
    current: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
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
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return Result.ok(data=new_user, message="用户创建成功")

@router.put("/users/{user_id}", response_model=Result[UserOut], summary="修改用户信息")
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
            roles = db.query(SysRole).filter(SysRole.id.in_(role_ids)).all()
            user.roles = roles

    for k, v in update_data.items():
        setattr(user, k, v)

    db.commit()
    db.refresh(user)
    return Result.ok(data=user, message="用户更新成功")

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

# ---------- 角色管理 ----------

@router.get("/roles", response_model=Result[List[RoleOut]], summary="获取系统角色列表")
def list_roles(db: Session = Depends(get_db)):
    roles = db.query(SysRole).filter(SysRole.is_deleted == 0).all()
    return Result.ok(data=roles)

# ---------- 菜单与动态路由树 ----------

@router.get("/menus/tree", response_model=Result[List[MenuOut]], summary="获取全量菜单树 (供底座侧边栏动态渲染)")
def get_menu_tree(db: Session = Depends(get_db)):
    all_menus = db.query(SysMenu).filter(
        SysMenu.is_deleted == 0,
        SysMenu.is_visible == 1
    ).order_by(SysMenu.sort_order.asc()).all()

    # 构建层级树
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
