from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.security import get_current_user_payload, get_current_superadmin
from app.core.scheduler import probe_single_service
from app.models.microservice import SysMicroservice
from app.schemas.common import Result, PageResult
from app.schemas.microservice import (
    MicroserviceCreate,
    MicroserviceUpdate,
    MicroserviceOut,
    HealthProbeResult
)

router = APIRouter(prefix="/microservices", tags=["03.微服务接入与健康治理"])

@router.get("", response_model=Result[PageResult[MicroserviceOut]], summary="分页/列表查询已接入的微服务")
def list_microservices(
    current: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(SysMicroservice).filter(SysMicroservice.is_deleted == 0)
    if keyword:
        query = query.filter(
            (SysMicroservice.service_code.ilike(f"%{keyword}%")) |
            (SysMicroservice.service_name.ilike(f"%{keyword}%"))
        )
    if category:
        query = query.filter(SysMicroservice.category == category)
    if status:
        query = query.filter(SysMicroservice.status == status)

    total = query.count()
    records = query.order_by(desc(SysMicroservice.id)).offset((current - 1) * size).limit(size).all()
    
    return Result.ok(data=PageResult(
        total=total,
        current=current,
        size=size,
        records=records
    ))

@router.get("/active", response_model=Result[List[MicroserviceOut]], summary="获取所有有效启用的微服务 (供动态路由与菜单渲染)")
def list_active_services(db: Session = Depends(get_db)):
    records = db.query(SysMicroservice).filter(
        SysMicroservice.is_deleted == 0,
        SysMicroservice.status == "ACTIVE"
    ).all()
    return Result.ok(data=records)

@router.post("/register", response_model=Result[MicroserviceOut], summary="注册新微服务能力 (支持主动注册或SuperAdmin手动录入)")
async def register_microservice(
    req: MicroserviceCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(SysMicroservice).filter(
        SysMicroservice.service_code == req.service_code,
        SysMicroservice.is_deleted == 0
    ).first()

    if existing:
        # 已存在则更新
        for k, v in req.model_dump(exclude_unset=True).items():
            setattr(existing, k, v)
        db.commit()
        db.refresh(existing)
        # 立即探测一次健康状态
        await probe_single_service(existing, db=db)
        return Result.ok(data=existing, message="微服务信息已更新")
    
    new_svc = SysMicroservice(**req.model_dump())
    db.add(new_svc)
    db.commit()
    db.refresh(new_svc)
    
    # 立即发起一次异步健康探测
    await probe_single_service(new_svc, db=db)
    db.refresh(new_svc)
    return Result.ok(data=new_svc, message="微服务接入注册成功")

@router.get("/{service_id}", response_model=Result[MicroserviceOut], summary="获取微服务详情")
def get_microservice(service_id: int, db: Session = Depends(get_db)):
    svc = db.query(SysMicroservice).filter(
        SysMicroservice.id == service_id,
        SysMicroservice.is_deleted == 0
    ).first()
    if not svc:
        return Result.fail("微服务不存在", code=404)
    return Result.ok(data=svc)

@router.put("/{service_id}", response_model=Result[MicroserviceOut], summary="修改微服务配置")
async def update_microservice(
    service_id: int,
    req: MicroserviceUpdate,
    db: Session = Depends(get_db)
):
    svc = db.query(SysMicroservice).filter(
        SysMicroservice.id == service_id,
        SysMicroservice.is_deleted == 0
    ).first()
    if not svc:
        return Result.fail("微服务不存在", code=404)

    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(svc, k, v)

    db.commit()
    db.refresh(svc)
    
    # 立即发起一次健康探测
    await probe_single_service(svc, db=db)
    db.refresh(svc)
    return Result.ok(data=svc, message="微服务配置修改成功")

@router.delete("/{service_id}", response_model=Result[bool], summary="注销/删除微服务")
def delete_microservice(
    service_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_superadmin)
):
    svc = db.query(SysMicroservice).filter(
        SysMicroservice.id == service_id,
        SysMicroservice.is_deleted == 0
    ).first()
    if not svc:
        return Result.fail("微服务不存在", code=404)

    svc.is_deleted = 1
    db.commit()
    return Result.ok(data=True, message="微服务已注销下线")

@router.post("/{service_id}/probe", response_model=Result[HealthProbeResult], summary="手动触发指定微服务实时健康探测")
async def probe_service_endpoint(
    service_id: int,
    db: Session = Depends(get_db)
):
    svc = db.query(SysMicroservice).filter(
        SysMicroservice.id == service_id,
        SysMicroservice.is_deleted == 0
    ).first()
    if not svc:
        return Result.fail("微服务不存在", code=404)

    res = await probe_single_service(svc, db=db)
    return Result.ok(data=res, message=f"健康探测完成: 状态={res.health_status}, 耗时={res.response_time_ms}ms")
