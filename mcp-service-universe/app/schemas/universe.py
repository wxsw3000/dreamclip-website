from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# ==================== Worldview Schemas ====================
class WorldviewBase(BaseModel):
    code: str = Field(..., description="唯一代码")
    title: str = Field(..., description="标题")
    subtitle: Optional[str] = None
    summary: str = Field(..., description="设定概要")
    description: Optional[str] = None
    banner_url: Optional[str] = None
    icon_url: Optional[str] = None
    theme_color: Optional[str] = "#6366f1"
    tags: Optional[str] = None
    sort_order: int = 0
    is_active: int = 1

class WorldviewCreate(WorldviewBase):
    pass

class WorldviewOut(WorldviewBase):
    id: int
    created_at: datetime
    character_count: Optional[int] = 0
    capsule_count: Optional[int] = 0
    chapter_count: Optional[int] = 0

    class Config:
        from_attributes = True

# ==================== Character Schemas ====================
class CharacterBase(BaseModel):
    worldview_id: int
    code: str
    name: str
    title: Optional[str] = None
    tagline: Optional[str] = None
    personality_color: str = "BLUE"
    zodiac: Optional[str] = None
    avatar_url: Optional[str] = None
    illustration_url: Optional[str] = None
    bio: str
    personality_desc: Optional[str] = None
    appearance_desc: Optional[str] = None
    details_json: Optional[Dict[str, Any]] = None
    sort_order: int = 0
    is_active: int = 1

class CharacterCreate(CharacterBase):
    pass

class CharacterOut(CharacterBase):
    id: int
    created_at: datetime
    worldview_title: Optional[str] = None

    class Config:
        from_attributes = True

# ==================== Emotion Capsule Schemas ====================
class EmotionCapsuleBase(BaseModel):
    worldview_id: int
    character_id: int
    title: str
    slug: str
    cover_image: Optional[str] = None
    summary: str
    content_md: str
    content_html: Optional[str] = None
    word_count: int = 0
    mood_tag: str = "治愈"
    mood_color: str = "BLUE"
    reading_time_mins: int = 3
    is_featured: int = 0
    is_published: int = 1

class EmotionCapsuleCreate(EmotionCapsuleBase):
    pass

class EmotionCapsuleOut(EmotionCapsuleBase):
    id: int
    view_count: int
    like_count: int
    published_at: datetime
    created_at: datetime
    character_name: Optional[str] = None
    character_avatar: Optional[str] = None
    worldview_title: Optional[str] = None

    class Config:
        from_attributes = True

# ==================== AVG Chapter Schemas ====================
class AvgChapterBase(BaseModel):
    worldview_id: int
    character_id: Optional[int] = None
    chapter_code: str
    chapter_name: str
    chapter_no: int = 1
    cover_image: Optional[str] = None
    summary: str
    game_url: str
    playtime_mins: int = 15
    is_free: int = 1
    is_published: int = 1
    sort_order: int = 0

class AvgChapterCreate(AvgChapterBase):
    pass

class AvgChapterOut(AvgChapterBase):
    id: int
    created_at: datetime
    worldview_title: Optional[str] = None
    character_name: Optional[str] = None

    class Config:
        from_attributes = True
