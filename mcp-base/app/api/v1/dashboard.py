from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.microservice import SysMicroservice
from app.models.user import SysUser
from app.models.dict_config import SysConfig
from app.models.log import SysLoginLog
from app.schemas.common import Result

router = APIRouter(prefix="/dashboard", tags=["02.控制台大盘统计"])

@router.get("/stats", response_model=Result[dict], summary="获取底座总览大盘统计数据 (单企业制造系统)")
def get_dashboard_stats(db: Session = Depends(get_db)):
    # 微服务统计
    total_services = db.query(func.count(SysMicroservice.id)).filter(SysMicroservice.is_deleted == 0).scalar() or 0
    healthy_services = db.query(func.count(SysMicroservice.id)).filter(
        SysMicroservice.is_deleted == 0,
        SysMicroservice.health_status == "HEALTHY"
    ).scalar() or 0
    down_services = db.query(func.count(SysMicroservice.id)).filter(
        SysMicroservice.is_deleted == 0,
        SysMicroservice.health_status == "DOWN"
    ).scalar() or 0

    # 系统运行参数数
    total_configs = db.query(func.count(SysConfig.id)).filter(SysConfig.is_deleted == 0).scalar() or 0

    # 用户统计
    total_users = db.query(func.count(SysUser.id)).filter(SysUser.is_deleted == 0).scalar() or 0

    # 最近登录日志
    recent_logins = db.query(SysLoginLog).order_by(SysLoginLog.login_time.desc()).limit(5).all()
    login_logs_data = [
        {
            "username": l.username,
            "status": l.status,
            "login_time": l.login_time.strftime("%Y-%m-%d %H:%M:%S") if l.login_time else "",
            "msg": l.msg
        } for l in recent_logins
    ]

    return Result.ok(data={
        "microservices": {
            "total": total_services,
            "healthy": healthy_services,
            "down": down_services,
            "rate": round((healthy_services / total_services * 100) if total_services > 0 else 100, 1)
        },
        "system": {
            "configs_count": total_configs,
            "status": "RUNNING"
        },
        "users": {
            "total": total_users
        },
        "recent_logins": login_logs_data
    })
