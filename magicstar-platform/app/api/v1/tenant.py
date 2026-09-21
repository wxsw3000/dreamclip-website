from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.security import get_current_superadmin
from app.models.tenant import SysTenant
from app.schemas.common import Result, PageResult
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantOut

router = APIRouter(prefix="/tenants", tags=["04.企业租户管理"])

@router.get("", response_model=Result[PageResult[TenantOut]], summary="分页查询企业租户档案")
def list_tenants(
    current: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    industry_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(SysTenant).filter(SysTenant.is_deleted == 0)
    if keyword:
        query = query.filter(
            (SysTenant.tenant_code.ilike(f"%{keyword}%")) |
            (SysTenant.tenant_name.ilike(f"%{keyword}%")) |
            (SysTenant.short_name.ilike(f"%{keyword}%"))
        )
    if industry_type:
        query = query.filter(SysTenant.industry_type == industry_type)
    if status:
        query = query.filter(SysTenant.status == status)

    total = query.count()
    records = query.order_by(desc(SysTenant.id)).offset((current - 1) * size).limit(size).all()
    
    return Result.ok(data=PageResult(
        total=total,
        current=current,
        size=size,
        records=records
    ))

@router.get("/active", response_model=Result[List[TenantOut]], summary="获取所有有效企业租户 (供全平台下拉切换)")
def list_active_tenants(db: Session = Depends(get_db)):
    records = db.query(SysTenant).filter(
        SysTenant.is_deleted == 0,
        SysTenant.status == "ACTIVE"
    ).all()
    return Result.ok(data=records)

@router.post("", response_model=Result[TenantOut], summary="开通/创建新企业租户")
def create_tenant(
    req: TenantCreate,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_superadmin)
):
    existing = db.query(SysTenant).filter(
        SysTenant.tenant_code == req.tenant_code,
        SysTenant.is_deleted == 0
    ).first()
    if existing:
        return Result.fail(f"企业租户编码 {req.tenant_code} 已存在", code=400)

    tenant = SysTenant(**req.model_dump())
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return Result.ok(data=tenant, message="企业租户开通成功")

@router.get("/{tenant_id}", response_model=Result[TenantOut], summary="获取指定租户详情")
def get_tenant(tenant_id: int, db: Session = Depends(get_db)):
    tenant = db.query(SysTenant).filter(
        SysTenant.id == tenant_id,
        SysTenant.is_deleted == 0
    ).first()
    if not tenant:
        return Result.fail("企业租户不存在", code=404)
    return Result.ok(data=tenant)

@router.put("/{tenant_id}", response_model=Result[TenantOut], summary="修改企业租户信息")
def update_tenant(
    tenant_id: int,
    req: TenantUpdate,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_superadmin)
):
    tenant = db.query(SysTenant).filter(
        SysTenant.id == tenant_id,
        SysTenant.is_deleted == 0
    ).first()
    if not tenant:
        return Result.fail("企业租户不存在", code=404)

    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(tenant, k, v)

    db.commit()
    db.refresh(tenant)
    return Result.ok(data=tenant, message="企业租户信息更新成功")

@router.delete("/{tenant_id}", response_model=Result[bool], summary="删除企业租户")
def delete_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_superadmin)
):
    tenant = db.query(SysTenant).filter(
        SysTenant.id == tenant_id,
        SysTenant.is_deleted == 0
    ).first()
    if not tenant:
        return Result.fail("企业租户不存在", code=404)

    tenant.is_deleted = 1
    db.commit()
    return Result.ok(data=True, message="企业租户已删除")
