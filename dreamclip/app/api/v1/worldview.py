from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.universe import Worldview, Character, EmotionCapsule, AvgChapter
from app.schemas.common import Result
from app.schemas.universe import WorldviewOut, WorldviewCreate

router = APIRouter(prefix="/worldviews", tags=["01.世界观管理"])

@router.get("", response_model=Result[List[WorldviewOut]], summary="获取世界观列表")
def list_worldviews(
    is_active: Optional[int] = Query(1, description="状态过滤"),
    db: Session = Depends(get_db)
):
    query = db.query(Worldview).filter(Worldview.is_deleted == 0)
    if is_active is not None:
        query = query.filter(Worldview.is_active == is_active)
    
    worldviews = query.order_by(Worldview.sort_order.asc(), Worldview.id.asc()).all()
    
    result_list = []
    for w in worldviews:
        char_count = db.query(func.count(Character.id)).filter(Character.worldview_id == w.id, Character.is_deleted == 0, Character.is_active == 1).scalar()
        caps_count = db.query(func.count(EmotionCapsule.id)).filter(EmotionCapsule.worldview_id == w.id, EmotionCapsule.is_deleted == 0, EmotionCapsule.is_published == 1).scalar()
        chap_count = db.query(func.count(AvgChapter.id)).filter(AvgChapter.worldview_id == w.id, AvgChapter.is_deleted == 0, AvgChapter.is_published == 1).scalar()
        
        w_dict = WorldviewOut.from_orm(w)
        w_dict.character_count = char_count
        w_dict.capsule_count = caps_count
        w_dict.chapter_count = chap_count
        result_list.append(w_dict)
        
    return Result.ok(data=result_list)

@router.get("/{identifier}", response_model=Result[WorldviewOut], summary="获取世界观详情 (支持ID或Code)")
def get_worldview(identifier: str, db: Session = Depends(get_db)):
    query = db.query(Worldview).filter(Worldview.is_deleted == 0)
    if identifier.isdigit():
        w = query.filter(Worldview.id == int(identifier)).first()
    else:
        w = query.filter(Worldview.code == identifier).first()
        
    if not w:
        return Result.fail("世界观不存在", code=404)
        
    char_count = db.query(func.count(Character.id)).filter(Character.worldview_id == w.id, Character.is_deleted == 0).scalar()
    caps_count = db.query(func.count(EmotionCapsule.id)).filter(EmotionCapsule.worldview_id == w.id, EmotionCapsule.is_deleted == 0).scalar()
    chap_count = db.query(func.count(AvgChapter.id)).filter(AvgChapter.worldview_id == w.id, AvgChapter.is_deleted == 0).scalar()
    
    w_out = WorldviewOut.from_orm(w)
    w_out.character_count = char_count
    w_out.capsule_count = caps_count
    w_out.chapter_count = chap_count
    return Result.ok(data=w_out)

@router.post("", response_model=Result[WorldviewOut], summary="新增世界观")
def create_worldview(req: WorldviewCreate, db: Session = Depends(get_db)):
    exist = db.query(Worldview).filter(Worldview.code == req.code, Worldview.is_deleted == 0).first()
    if exist:
        return Result.fail(f"世界观代码 '{req.code}' 已存在", code=400)
        
    w = Worldview(**req.dict())
    db.add(w)
    db.commit()
    db.refresh(w)
    return Result.ok(data=WorldviewOut.from_orm(w), message="世界观创建成功")
