from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_superadmin
from app.models.dict_config import SysDictType, SysDictData, SysConfig
from app.schemas.common import Result
from app.schemas.dict_config import DictTypeOut, DictDataOut, ConfigOut, ConfigUpdate

router = APIRouter(prefix="/system", tags=["06.字典与全局参数设置"])

@router.get("/dicts/types", response_model=Result[List[DictTypeOut]], summary="获取所有字典类型列表")
def list_dict_types(db: Session = Depends(get_db)):
    types = db.query(SysDictType).filter(SysDictType.is_deleted == 0).all()
    return Result.ok(data=types)

@router.get("/dicts/data/{dict_code}", response_model=Result[List[DictDataOut]], summary="根据字典编码获取字典数据项 (如 industry_type)")
def get_dict_data_by_code(dict_code: str, db: Session = Depends(get_db)):
    data = db.query(SysDictData).filter(
        SysDictData.dict_code == dict_code,
        SysDictData.is_deleted == 0,
        SysDictData.status == "ACTIVE"
    ).order_by(SysDictData.sort_order.asc()).all()
    return Result.ok(data=data)

@router.get("/configs", response_model=Result[List[ConfigOut]], summary="获取平台全局运行配置列表")
def list_configs(db: Session = Depends(get_db)):
    configs = db.query(SysConfig).filter(SysConfig.is_deleted == 0).all()
    return Result.ok(data=configs)

@router.put("/configs/{config_key}", response_model=Result[ConfigOut], summary="更新指定平台参数")
def update_config(
    config_key: str,
    req: ConfigUpdate,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_superadmin)
):
    cfg = db.query(SysConfig).filter(
        SysConfig.config_key == config_key,
        SysConfig.is_deleted == 0
    ).first()
    if not cfg:
        return Result.fail("参数不存在", code=404)

    cfg.config_value = req.config_value
    if req.remark is not None:
        cfg.remark = req.remark

    db.commit()
    db.refresh(cfg)
    return Result.ok(data=cfg, message="参数修改成功")
