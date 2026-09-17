from sqlalchemy import Column, String, Integer, BigInteger, Text, SmallInteger, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import BaseModel

class Worldview(BaseModel):
    """世界观大IP体系表"""
    __tablename__ = "uc_worldviews"

    code = Column(String(64), unique=True, nullable=False, index=True, comment="世界观唯一标识代码 (如 nebula-chronicles, cyber-mail)")
    title = Column(String(128), nullable=False, comment="世界观主标题 (如 星云纪元 / 记忆信箱)")
    subtitle = Column(String(255), nullable=True, comment="副标题或一句话理念")
    summary = Column(Text, nullable=False, comment="世界观基础设定与故事背景简述")
    description = Column(Text, nullable=True, comment="详细世界观与编年史 (Markdown)")
    banner_url = Column(String(500), nullable=True, comment="主视觉横幅背景图URL")
    icon_url = Column(String(500), nullable=True, comment="世界观徽章图标URL")
    theme_color = Column(String(32), default="#6366f1", nullable=True, comment="主色调 (Hex色值)")
    tags = Column(String(255), nullable=True, comment="标签 (以逗号分隔，如 科幻,情感,冒险)")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序权重")
    is_active = Column(SmallInteger, default=1, nullable=False, comment="是否启用 (1-是, 0-否)")

    characters = relationship("Character", back_populates="worldview", cascade="all, delete-orphan")
    capsules = relationship("EmotionCapsule", back_populates="worldview")
    chapters = relationship("AvgChapter", back_populates="worldview")

class Character(BaseModel):
    """角色档案表"""
    __tablename__ = "uc_characters"

    worldview_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("uc_worldviews.id"), nullable=False, index=True)
    code = Column(String(64), unique=True, nullable=False, index=True, comment="角色代码 (如 raven, lunaria, cipher)")
    name = Column(String(64), nullable=False, comment="角色名字")
    title = Column(String(128), nullable=True, comment="角色称号/头衔 (如 深夜记忆修补师, 星图观测者)")
    tagline = Column(String(255), nullable=True, comment="角色核心名言/台词")
    personality_color = Column(String(32), default="BLUE", nullable=False, comment="性格色彩 (RED-烈焰开拓, BLUE-静谧理性, YELLOW-璀璨治愈, GREEN-深林共情)")
    zodiac = Column(String(32), nullable=True, comment="星座属性 (如 天秤座, 天蝎座)")
    avatar_url = Column(String(500), nullable=True, comment="角色头像URL")
    illustration_url = Column(String(500), nullable=True, comment="角色全身/立绘图URL")
    bio = Column(Text, nullable=False, comment="角色简述与背景故事")
    personality_desc = Column(Text, nullable=True, comment="性格深度解析")
    appearance_desc = Column(Text, nullable=True, comment="外貌与穿搭特征")
    details_json = Column(JSON, nullable=True, comment="扩展属性 JSON (如 年龄、偏好物品、技能、属性值)")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序权重")
    is_active = Column(SmallInteger, default=1, nullable=False, comment="是否启用 (1-是, 0-否)")

    worldview = relationship("Worldview", back_populates="characters")
    capsules = relationship("EmotionCapsule", back_populates="character")
    chapters = relationship("AvgChapter", back_populates="character")

class EmotionCapsule(BaseModel):
    """情绪胶囊图文表 (800~1500字原创小品，主攻 AdSense 内容审核)"""
    __tablename__ = "uc_emotion_capsules"

    worldview_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("uc_worldviews.id"), nullable=False, index=True)
    character_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("uc_characters.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False, comment="情绪胶囊标题")
    slug = Column(String(128), unique=True, nullable=False, index=True, comment="URL友好的文章唯一标识")
    cover_image = Column(String(500), nullable=True, comment="故事封面配图URL")
    summary = Column(Text, nullable=False, comment="情绪引言/摘要 (用于卡片展示与SEO描述)")
    content_md = Column(Text, nullable=False, comment="文章正文 (Markdown格式，800~1500字深度原创)")
    content_html = Column(Text, nullable=True, comment="渲染后的 HTML 正文 (加速SEO爬取与页面直出)")
    word_count = Column(Integer, default=0, nullable=False, comment="正文字数统计")
    mood_tag = Column(String(64), default="治愈", nullable=False, comment="情绪标签 (如 治愈, 孤独, 勇气, 释怀, 温暖)")
    mood_color = Column(String(32), default="BLUE", nullable=False, comment="情绪色彩标签")
    reading_time_mins = Column(Integer, default=3, comment="预计阅读时长(分钟)")
    view_count = Column(Integer, default=0, nullable=False, comment="阅读浏览次数")
    like_count = Column(Integer, default=0, nullable=False, comment="点赞共鸣数")
    is_featured = Column(SmallInteger, default=0, nullable=False, comment="是否首页精选推荐 (1-是, 0-否)")
    is_published = Column(SmallInteger, default=1, nullable=False, comment="是否公开发布 (1-已发布, 0-草稿)")
    published_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="发布时间")

    worldview = relationship("Worldview", back_populates="capsules")
    character = relationship("Character", back_populates="capsules")

class AvgChapter(BaseModel):
    """AVG 游戏章节元数据表 (独立 HTML5 游戏分发元数据)"""
    __tablename__ = "uc_avg_chapters"

    worldview_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("uc_worldviews.id"), nullable=False, index=True)
    character_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("uc_characters.id"), nullable=True, index=True)
    chapter_code = Column(String(64), unique=True, nullable=False, index=True, comment="章节唯一代码 (如 ch1-memory-origin)")
    chapter_name = Column(String(128), nullable=False, comment="章节名称 (如 第一章：最初的遗失信件)")
    chapter_no = Column(Integer, default=1, nullable=False, comment="章节序号 (1, 2, 3...)")
    cover_image = Column(String(500), nullable=True, comment="游戏章节海报封面")
    summary = Column(Text, nullable=False, comment="章节故事简介与玩法提示")
    game_url = Column(String(500), nullable=False, comment="独立 HTML5 游戏运行地址 (如 /games/demo-avg/index.html 或外部独立链接)")
    playtime_mins = Column(Integer, default=15, comment="预计游玩时长(分钟)")
    is_free = Column(SmallInteger, default=1, nullable=False, comment="是否免费体验 (1-免费, 0-需解锁)")
    is_published = Column(SmallInteger, default=1, nullable=False, comment="是否上线发布 (1-上线, 0-未上线)")
    sort_order = Column(Integer, default=0, nullable=False, comment="展示排序")

    worldview = relationship("Worldview", back_populates="chapters")
    character = relationship("Character", back_populates="chapters")
