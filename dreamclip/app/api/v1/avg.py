from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.universe import AvgChapter, Worldview, Character
from app.schemas.common import Result
from app.schemas.universe import AvgChapterOut, AvgChapterCreate, AvgChapterUpdate

router = APIRouter(prefix="/avg", tags=["04.AVG游戏章节"])

@router.get("/chapters", response_model=Result[List[AvgChapterOut]], summary="获取AVG游戏章节列表")
def list_chapters(
    worldview_id: Optional[int] = Query(None, description="所属世界观ID"),
    character_id: Optional[int] = Query(None, description="登场主角ID"),
    is_published: Optional[int] = Query(None, description="发布状态"),
    db: Session = Depends(get_db)
):
    query = db.query(AvgChapter).filter(AvgChapter.is_deleted == 0)
    if worldview_id:
        query = query.filter(AvgChapter.worldview_id == worldview_id)
    if character_id:
        query = query.filter(AvgChapter.character_id == character_id)
    if is_published is not None:
        query = query.filter(AvgChapter.is_published == is_published)

    chapters = query.order_by(AvgChapter.sort_order.asc(), AvgChapter.chapter_no.asc()).all()

    result = []
    for ch in chapters:
        out = AvgChapterOut.from_orm(ch)
        if ch.worldview:
            out.worldview_title = ch.worldview.title
        if ch.character:
            out.character_name = ch.character.name
        result.append(out)

    return Result.ok(data=result)

@router.get("/chapters/{chapter_code}", response_model=Result[AvgChapterOut], summary="获取特定AVG游戏章节元数据")
def get_chapter(chapter_code: str, db: Session = Depends(get_db)):
    query = db.query(AvgChapter).filter(AvgChapter.is_deleted == 0)
    if chapter_code.isdigit():
        ch = query.filter(AvgChapter.id == int(chapter_code)).first()
    else:
        ch = query.filter(AvgChapter.chapter_code == chapter_code).first()

    if not ch:
        return Result.fail("游戏章节不存在", code=404)

    out = AvgChapterOut.from_orm(ch)
    if ch.worldview:
        out.worldview_title = ch.worldview.title
    if ch.character:
        out.character_name = ch.character.name
    return Result.ok(data=out)

@router.post("/chapters", response_model=Result[AvgChapterOut], summary="登记新的AVG游戏章节")
def create_chapter(req: AvgChapterCreate, db: Session = Depends(get_db)):
    exist = db.query(AvgChapter).filter(AvgChapter.chapter_code == req.chapter_code, AvgChapter.is_deleted == 0).first()
    if exist:
        return Result.fail(f"章节代码 '{req.chapter_code}' 已存在", code=400)

    ch = AvgChapter(**req.dict())
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return Result.ok(data=AvgChapterOut.from_orm(ch), message="AVG 游戏章节登记成功")

@router.put("/chapters/{id}", response_model=Result[AvgChapterOut], summary="更新AVG游戏章节")
def update_chapter(id: int, req: AvgChapterUpdate, db: Session = Depends(get_db)):
    ch = db.query(AvgChapter).filter(AvgChapter.id == id, AvgChapter.is_deleted == 0).first()
    if not ch:
        return Result.fail("游戏章节不存在", code=404)

    update_data = req.dict(exclude_unset=True)
    if "chapter_code" in update_data and update_data["chapter_code"] != ch.chapter_code:
        exist = db.query(AvgChapter).filter(AvgChapter.chapter_code == update_data["chapter_code"], AvgChapter.id != id, AvgChapter.is_deleted == 0).first()
        if exist:
            return Result.fail(f"章节代码 '{update_data['chapter_code']}' 已被占用", code=400)

    for k, v in update_data.items():
        setattr(ch, k, v)

    db.commit()
    db.refresh(ch)
    return Result.ok(data=AvgChapterOut.from_orm(ch), message="游戏章节更新成功")

@router.post("/chapters/{id}/toggle", response_model=Result[AvgChapterOut], summary="切换AVG章节发布状态")
def toggle_chapter_status(id: int, db: Session = Depends(get_db)):
    ch = db.query(AvgChapter).filter(AvgChapter.id == id, AvgChapter.is_deleted == 0).first()
    if not ch:
        return Result.fail("游戏章节不存在", code=404)
    ch.is_published = 0 if ch.is_published == 1 else 1
    db.commit()
    db.refresh(ch)
    status_text = "已上线" if ch.is_published == 1 else "已下线/草稿"
    return Result.ok(data=AvgChapterOut.from_orm(ch), message=f"状态切换为：{status_text}")

@router.delete("/chapters/{id}", response_model=Result[bool], summary="删除AVG游戏章节")
def delete_chapter(id: int, db: Session = Depends(get_db)):
    ch = db.query(AvgChapter).filter(AvgChapter.id == id, AvgChapter.is_deleted == 0).first()
    if not ch:
        return Result.fail("游戏章节不存在", code=404)
    ch.is_deleted = 1
    db.commit()
    return Result.ok(data=True, message="删除成功")

