from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.universe import EmotionCapsule, Character, Worldview
from app.schemas.common import Result, PageResult
from app.schemas.universe import EmotionCapsuleOut, EmotionCapsuleCreate, EmotionCapsuleUpdate

router = APIRouter(prefix="/capsules", tags=["03.情绪胶囊图文"])

@router.get("", response_model=Result[PageResult[EmotionCapsuleOut]], summary="获取情绪胶囊列表 (支持分页、角色、情绪筛选)")
def list_capsules(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页大小"),
    worldview_id: Optional[int] = Query(None, description="所属世界观ID"),
    character_id: Optional[int] = Query(None, description="所属角色ID"),
    mood_tag: Optional[str] = Query(None, description="情绪标签 (治愈/孤独/勇气等)"),
    mood_color: Optional[str] = Query(None, description="情绪色彩 (RED/BLUE/YELLOW/GREEN)"),
    is_featured: Optional[int] = Query(None, description="是否精选推荐"),
    is_published: Optional[int] = Query(None, description="发布状态"),
    db: Session = Depends(get_db)
):
    query = db.query(EmotionCapsule).filter(EmotionCapsule.is_deleted == 0)
    if worldview_id:
        query = query.filter(EmotionCapsule.worldview_id == worldview_id)
    if character_id:
        query = query.filter(EmotionCapsule.character_id == character_id)
    if mood_tag:
        query = query.filter(EmotionCapsule.mood_tag == mood_tag)
    if mood_color:
        query = query.filter(EmotionCapsule.mood_color == mood_color.upper())
    if is_featured is not None:
        query = query.filter(EmotionCapsule.is_featured == is_featured)
    if is_published is not None:
        query = query.filter(EmotionCapsule.is_published == is_published)

    total = query.count()
    capsules = query.order_by(EmotionCapsule.published_at.desc())\
                    .offset((page - 1) * page_size)\
                    .limit(page_size)\
                    .all()

    items = []
    for c in capsules:
        out = EmotionCapsuleOut.from_orm(c)
        if c.character:
            out.character_name = c.character.name
            out.character_avatar = c.character.avatar_url
        if c.worldview:
            out.worldview_title = c.worldview.title
        items.append(out)

    page_data = PageResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )
    return Result.ok(data=page_data)

@router.get("/{identifier}", response_model=Result[EmotionCapsuleOut], summary="获取情绪胶囊正文 (支持ID或Slug，自动增加阅读量)")
def get_capsule(identifier: str, db: Session = Depends(get_db)):
    query = db.query(EmotionCapsule).filter(EmotionCapsule.is_deleted == 0)
    if identifier.isdigit():
        c = query.filter(EmotionCapsule.id == int(identifier)).first()
    else:
        c = query.filter(EmotionCapsule.slug == identifier).first()

    if not c:
        return Result.fail("情绪胶囊不存在", code=404)

    # 递增阅读量
    c.view_count += 1
    db.commit()
    db.refresh(c)

    out = EmotionCapsuleOut.from_orm(c)
    if c.character:
        out.character_name = c.character.name
        out.character_avatar = c.character.avatar_url
    if c.worldview:
        out.worldview_title = c.worldview.title
    return Result.ok(data=out)

@router.post("/{id}/like", response_model=Result[int], summary="点赞/共鸣情绪胶囊")
def like_capsule(id: int, db: Session = Depends(get_db)):
    c = db.query(EmotionCapsule).filter(EmotionCapsule.id == id, EmotionCapsule.is_deleted == 0).first()
    if not c:
        return Result.fail("情绪胶囊不存在", code=404)
    c.like_count += 1
    db.commit()
    return Result.ok(data=c.like_count, message="共鸣成功 +1")

@router.post("", response_model=Result[EmotionCapsuleOut], summary="发布新的情绪胶囊小品")
def create_capsule(req: EmotionCapsuleCreate, db: Session = Depends(get_db)):
    exist = db.query(EmotionCapsule).filter(EmotionCapsule.slug == req.slug, EmotionCapsule.is_deleted == 0).first()
    if exist:
        return Result.fail(f"文章Slug '{req.slug}' 已被占用", code=400)

    # 计算字数与阅读时长
    word_count = len(req.content_md) if req.content_md else 0
    reading_time = max(1, word_count // 300)

    c = EmotionCapsule(**req.dict())
    c.word_count = word_count
    c.reading_time_mins = reading_time
    db.add(c)
    db.commit()
    db.refresh(c)
    return Result.ok(data=EmotionCapsuleOut.from_orm(c), message="情绪胶囊发布成功")

@router.put("/{id}", response_model=Result[EmotionCapsuleOut], summary="更新情绪胶囊")
def update_capsule(id: int, req: EmotionCapsuleUpdate, db: Session = Depends(get_db)):
    c = db.query(EmotionCapsule).filter(EmotionCapsule.id == id, EmotionCapsule.is_deleted == 0).first()
    if not c:
        return Result.fail("情绪胶囊不存在", code=404)

    update_data = req.dict(exclude_unset=True)
    if "slug" in update_data and update_data["slug"] != c.slug:
        exist = db.query(EmotionCapsule).filter(EmotionCapsule.slug == update_data["slug"], EmotionCapsule.id != id, EmotionCapsule.is_deleted == 0).first()
        if exist:
            return Result.fail(f"Slug '{update_data['slug']}' 已被占用", code=400)

    if "content_md" in update_data and update_data["content_md"]:
        update_data["word_count"] = len(update_data["content_md"])
        update_data["reading_time_mins"] = max(1, update_data["word_count"] // 300)

    for k, v in update_data.items():
        setattr(c, k, v)

    db.commit()
    db.refresh(c)
    return Result.ok(data=EmotionCapsuleOut.from_orm(c), message="更新成功")

@router.post("/{id}/toggle", response_model=Result[EmotionCapsuleOut], summary="切换发布/草稿状态")
def toggle_capsule_status(id: int, db: Session = Depends(get_db)):
    c = db.query(EmotionCapsule).filter(EmotionCapsule.id == id, EmotionCapsule.is_deleted == 0).first()
    if not c:
        return Result.fail("情绪胶囊不存在", code=404)
    c.is_published = 0 if c.is_published == 1 else 1
    db.commit()
    db.refresh(c)
    status_text = "已发布上线" if c.is_published == 1 else "已转为草稿"
    return Result.ok(data=EmotionCapsuleOut.from_orm(c), message=f"状态切换为：{status_text}")

@router.delete("/{id}", response_model=Result[bool], summary="删除情绪胶囊")
def delete_capsule(id: int, db: Session = Depends(get_db)):
    c = db.query(EmotionCapsule).filter(EmotionCapsule.id == id, EmotionCapsule.is_deleted == 0).first()
    if not c:
        return Result.fail("情绪胶囊不存在", code=404)
    c.is_deleted = 1
    db.commit()
    return Result.ok(data=True, message="删除成功")

