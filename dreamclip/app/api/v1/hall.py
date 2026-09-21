from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.universe import HallBanner
from app.schemas.common import Result
from app.schemas.universe import HallBannerOut, HallBannerCreate, HallBannerUpdate

router = APIRouter(prefix="/hall/banners", tags=["05.梦之厅焦点图文跑马灯"])

DEFAULT_SEED_BANNERS = [
    {
        "title": "打捞星穹深处每一粒失落的情绪胶囊",
        "subtitle": "在新安托利亚的微光夜色中，跟随深夜修补师与星轨植物学家，重启那些未曾褪色的真实心跳。",
        "badge_text": "✨ 梦之厅首发",
        "image_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=1200&auto=format&fit=crop",
        "link_url": "/#capsules-stream",
        "theme_color": "#6366f1",
        "sort_order": 100,
        "is_active": 1
    },
    {
        "title": "《深空信箱：2099》核心世界观与角色群像全景",
        "subtitle": "探索雷文、露娜莉亚与伊格尼斯的跨维度故事线，在情绪晶体中寻找旧地球失落的记忆信件。",
        "badge_text": "🌌 角色宇宙",
        "image_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?q=80&w=1200&auto=format&fit=crop",
        "link_url": "/#characters-stream",
        "theme_color": "#06b6d4",
        "sort_order": 90,
        "is_active": 1
    },
    {
        "title": "AVG 章节游戏：第一章《失落的深空信标》现已开放",
        "subtitle": "纯粹 HTML5 标准轻量化交互体验，无缝接入 DreamClip 统一身份，做出你的关键命运抉择。",
        "badge_text": "🎮 沉浸剧场",
        "image_url": "https://images.unsplash.com/photo-1578632767115-351597cf2477?q=80&w=1200&auto=format&fit=crop",
        "link_url": "/games",
        "theme_color": "#ec4899",
        "sort_order": 80,
        "is_active": 1
    }
]

def ensure_seed_banners(db: Session):
    count = db.query(HallBanner).filter(HallBanner.is_deleted == 0).count()
    if count == 0:
        for item in DEFAULT_SEED_BANNERS:
            b = HallBanner(
                title=item["title"],
                subtitle=item["subtitle"],
                badge_text=item["badge_text"],
                image_url=item["image_url"],
                link_url=item["link_url"],
                theme_color=item["theme_color"],
                sort_order=item["sort_order"],
                is_active=item["is_active"]
            )
            db.add(b)
        db.commit()

@router.get("", response_model=Result[List[HallBannerOut]], summary="获取梦之厅焦点跑马灯列表")
def list_hall_banners(
    all_status: bool = Query(False, description="是否获取全量状态（含已下线，用于后台管理）"),
    db: Session = Depends(get_db)
):
    ensure_seed_banners(db)
    query = db.query(HallBanner).filter(HallBanner.is_deleted == 0)
    if not all_status:
        query = query.filter(HallBanner.is_active == 1)
    
    banners = query.order_by(HallBanner.sort_order.desc(), HallBanner.id.desc()).all()
    items = [HallBannerOut.from_orm(b) for b in banners]
    return Result.ok(data=items)

@router.post("", response_model=Result[HallBannerOut], summary="新增梦之厅焦点图文")
def create_hall_banner(req: HallBannerCreate, db: Session = Depends(get_db)):
    b = HallBanner(
        title=req.title.strip(),
        subtitle=req.subtitle.strip() if req.subtitle else None,
        badge_text=req.badge_text.strip() if req.badge_text else "✨ 梦之焦点",
        image_url=req.image_url.strip() if req.image_url else None,
        link_url=req.link_url.strip() if req.link_url else "/#capsules-stream",
        theme_color=req.theme_color.strip() if req.theme_color else "#6366f1",
        sort_order=req.sort_order,
        is_active=req.is_active
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return Result.ok(data=HallBannerOut.from_orm(b), message="添加焦点图文成功")

@router.put("/{id}", response_model=Result[HallBannerOut], summary="更新梦之厅焦点图文")
def update_hall_banner(id: int, req: HallBannerUpdate, db: Session = Depends(get_db)):
    b = db.query(HallBanner).filter(HallBanner.id == id, HallBanner.is_deleted == 0).first()
    if not b:
        return Result.fail("焦点图文不存在", code=404)
    
    if req.title is not None:
        b.title = req.title.strip()
    if req.subtitle is not None:
        b.subtitle = req.subtitle.strip()
    if req.badge_text is not None:
        b.badge_text = req.badge_text.strip()
    if req.image_url is not None:
        b.image_url = req.image_url.strip()
    if req.link_url is not None:
        b.link_url = req.link_url.strip()
    if req.theme_color is not None:
        b.theme_color = req.theme_color.strip()
    if req.sort_order is not None:
        b.sort_order = req.sort_order
    if req.is_active is not None:
        b.is_active = req.is_active

    db.commit()
    db.refresh(b)
    return Result.ok(data=HallBannerOut.from_orm(b), message="更新焦点图文成功")

@router.post("/{id}/toggle", response_model=Result[HallBannerOut], summary="切换焦点图文上下线状态")
def toggle_hall_banner(id: int, db: Session = Depends(get_db)):
    b = db.query(HallBanner).filter(HallBanner.id == id, HallBanner.is_deleted == 0).first()
    if not b:
        return Result.fail("焦点图文不存在", code=404)
    b.is_active = 0 if b.is_active == 1 else 1
    db.commit()
    db.refresh(b)
    status_text = "上线展示" if b.is_active == 1 else "下线隐藏"
    return Result.ok(data=HallBannerOut.from_orm(b), message=f"已切换为：{status_text}")

@router.delete("/{id}", response_model=Result[bool], summary="删除梦之厅焦点图文")
def delete_hall_banner(id: int, db: Session = Depends(get_db)):
    b = db.query(HallBanner).filter(HallBanner.id == id, HallBanner.is_deleted == 0).first()
    if not b:
        return Result.fail("焦点图文不存在", code=404)
    b.is_deleted = 1
    db.commit()
    return Result.ok(data=True, message="删除成功")
