from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.universe import Character, Worldview
from app.schemas.common import Result
from app.schemas.universe import CharacterOut, CharacterCreate, CharacterUpdate

router = APIRouter(prefix="/characters", tags=["02.角色档案管理"])

@router.get("", response_model=Result[List[CharacterOut]], summary="获取角色列表 (支持按世界观、性格色彩、星座筛选)")
def list_characters(
    worldview_id: Optional[int] = Query(None, description="所属世界观ID"),
    personality_color: Optional[str] = Query(None, description="性格色彩过滤 (RED/BLUE/YELLOW/GREEN)"),
    zodiac: Optional[str] = Query(None, description="星座过滤"),
    is_active: Optional[int] = Query(None, description="状态"),
    db: Session = Depends(get_db)
):
    query = db.query(Character).filter(Character.is_deleted == 0)
    if worldview_id:
        query = query.filter(Character.worldview_id == worldview_id)
    if personality_color:
        query = query.filter(Character.personality_color == personality_color.upper())
    if zodiac:
        query = query.filter(Character.zodiac == zodiac)
    if is_active is not None:
        query = query.filter(Character.is_active == is_active)
        
    chars = query.order_by(Character.sort_order.asc(), Character.id.asc()).all()
    
    result = []
    for c in chars:
        out = CharacterOut.from_orm(c)
        if c.worldview:
            out.worldview_title = c.worldview.title
        result.append(out)
        
    return Result.ok(data=result)

@router.get("/{identifier}", response_model=Result[CharacterOut], summary="获取角色档案详情 (支持ID或Code)")
def get_character(identifier: str, db: Session = Depends(get_db)):
    query = db.query(Character).filter(Character.is_deleted == 0)
    if identifier.isdigit():
        c = query.filter(Character.id == int(identifier)).first()
    else:
        c = query.filter(Character.code == identifier).first()
        
    if not c:
        return Result.fail("角色档案不存在", code=404)
        
    out = CharacterOut.from_orm(c)
    if c.worldview:
        out.worldview_title = c.worldview.title
    return Result.ok(data=out)

@router.post("", response_model=Result[CharacterOut], summary="新增角色档案")
def create_character(req: CharacterCreate, db: Session = Depends(get_db)):
    exist = db.query(Character).filter(Character.code == req.code, Character.is_deleted == 0).first()
    if exist:
        return Result.fail(f"角色代码 '{req.code}' 已存在", code=400)
        
    c = Character(**req.dict())
    db.add(c)
    db.commit()
    db.refresh(c)
    return Result.ok(data=CharacterOut.from_orm(c), message="角色档案创建成功")

@router.put("/{id}", response_model=Result[CharacterOut], summary="更新角色档案")
def update_character(id: int, req: CharacterUpdate, db: Session = Depends(get_db)):
    c = db.query(Character).filter(Character.id == id, Character.is_deleted == 0).first()
    if not c:
        return Result.fail("角色档案不存在", code=404)

    update_data = req.dict(exclude_unset=True)
    if "code" in update_data and update_data["code"] != c.code:
        exist = db.query(Character).filter(Character.code == update_data["code"], Character.id != id, Character.is_deleted == 0).first()
        if exist:
            return Result.fail(f"角色代码 '{update_data['code']}' 已被占用", code=400)

    for k, v in update_data.items():
        setattr(c, k, v)

    db.commit()
    db.refresh(c)
    return Result.ok(data=CharacterOut.from_orm(c), message="角色更新成功")

@router.post("/{id}/toggle", response_model=Result[CharacterOut], summary="切换角色启用状态")
def toggle_character_status(id: int, db: Session = Depends(get_db)):
    c = db.query(Character).filter(Character.id == id, Character.is_deleted == 0).first()
    if not c:
        return Result.fail("角色档案不存在", code=404)
    c.is_active = 0 if c.is_active == 1 else 1
    db.commit()
    db.refresh(c)
    status_text = "已启用" if c.is_active == 1 else "已停用"
    return Result.ok(data=CharacterOut.from_orm(c), message=f"状态切换为：{status_text}")

@router.delete("/{id}", response_model=Result[bool], summary="删除角色档案")
def delete_character(id: int, db: Session = Depends(get_db)):
    c = db.query(Character).filter(Character.id == id, Character.is_deleted == 0).first()
    if not c:
        return Result.fail("角色档案不存在", code=404)
    c.is_deleted = 1
    db.commit()
    return Result.ok(data=True, message="删除成功")

