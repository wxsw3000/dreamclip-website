import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.core.register import register_to_base
from app.models.universe import Worldview, Character, EmotionCapsule, AvgChapter, HallBanner
from app.api.v1.hall import ensure_seed_banners
from app.api.v1.router import api_v1_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("dreamclip")

def init_seed_universe_data():
    """初始化数据库表并注入基础的世界观与角色数据"""
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        wv_count = db.query(Worldview).count()
        if wv_count == 0:
            # 1. 种子世界观：星穹记忆与情绪信箱
            wv1 = Worldview(
                code="cyber-mail-2099",
                title="深空信箱：2099",
                subtitle="在遗忘的星穹边缘，打捞被世界遗弃的情绪信件",
                summary="近未来深空浮空都市中，人类的情绪与记忆被数字化封存为「情绪胶囊」。特殊的信使与修补师们穿梭在星轨夜色中，寻找失落的情感共鸣。",
                description="""### 世界观编年史
2099 年，浮空城「新安托利亚」成为人类文明最后的梦境庇护所。
这里没有眼泪，因为所有激烈、痛苦或温柔的情绪都被抽取并精炼成了发光的晶体胶囊。
然而，仍有一群被称为「情绪潜行者」与「深空信使」的人，在城市的最底层修复那些残存的真实心跳。""",
                banner_url="https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=1200&auto=format&fit=crop",
                icon_url="https://api.iconify.design/lucide:mail-search.svg?color=%23818cf8",
                theme_color="#6366f1",
                tags="科幻,治愈,悬疑,情绪共鸣",
                sort_order=1,
                is_active=1
            )
            db.add(wv1)
            db.commit()
            db.refresh(wv1)

            # 2. 种子角色：3 位不同性格色彩与星座的角色
            c1 = Character(
                worldview_id=wv1.id,
                code="raven-07",
                name="雷文 (Raven)",
                title="深夜情绪修补师",
                tagline="“不是所有破碎的心，都需要被恢复成原来的样子。”",
                personality_color="BLUE",
                zodiac="天蝎座",
                avatar_url="https://api.dicebear.com/7.x/bottts/svg?seed=Raven07&backgroundColor=0284c7",
                illustration_url="https://images.unsplash.com/photo-1578632767115-351597cf2477?q=80&w=800&auto=format&fit=crop",
                bio="冷峻少言的深空机械信使，拥有读取情绪残晶的特殊义眼。习惯在凌晨三点的新安托利亚下层街区出没。",
                personality_desc="理性、克制、外冷内热，擅长在纷乱的数据流中精准捕捉最纯粹的情感波动。",
                appearance_desc="黑色长风衣，右眼嵌有泛着幽蓝光芒的晶体义眼，随身携带着黄铜色的记忆收集箱。",
                details_json={"age": 26, "favorite_drink": "合成黑咖啡", "special_ability": "共感解析"},
                sort_order=1,
                is_active=1
            )
            c2 = Character(
                worldview_id=wv1.id,
                code="lunaria",
                name="露娜莉亚 (Lunaria)",
                title="星轨植物学家与梦境抚慰者",
                tagline="“即便是在没有太阳的星环上，情绪的花朵依然会向光生长。”",
                personality_color="YELLOW",
                zodiac="双鱼座",
                avatar_url="https://api.dicebear.com/7.x/bottts/svg?seed=Lunaria&backgroundColor=f59e0b",
                illustration_url="https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=800&auto=format&fit=crop",
                bio="在浮空温室中培育发光情绪花草的少女。她的花朵能根据周围人的心情改变芳香与色彩。",
                personality_desc="温暖、治愈、富有同理心，总能用最柔和的话语化解他人的焦虑与孤独。",
                appearance_desc="亚麻色长卷发，佩戴星芒发饰，长裙边缘点缀着微光的夜光花瓣。",
                details_json={"age": 21, "hobby": "收集雨声录音", "special_ability": "心灵抚慰"},
                sort_order=2,
                is_active=1
            )
            c3 = Character(
                worldview_id=wv1.id,
                code="ignis",
                name="伊格尼斯 (Ignis)",
                title="废土引擎开拓者",
                tagline="“只要火花还在跳动，黑夜就永远无法吞没前路！”",
                personality_color="RED",
                zodiac="白羊座",
                avatar_url="https://api.dicebear.com/7.x/bottts/svg?seed=Ignis&backgroundColor=ef4444",
                illustration_url="https://images.unsplash.com/photo-1563089145-599997674d42?q=80&w=800&auto=format&fit=crop",
                bio="驾驶重型悬浮机车的先锋探索者，性格豪迈热烈，致力于打通通往旧大陆的能量通路。",
                personality_desc="果敢、无畏、行动派，对伙伴极度忠诚，充满感染力。",
                appearance_desc="赤红色短发，护目镜推在额头上，身上带着机油与电火花的轻微焦香。",
                details_json={"age": 24, "vehicle": "猩红推进器Mark-IV", "weapon": "等离子喷射扳手"},
                sort_order=3,
                is_active=1
            )
            db.add_all([c1, c2, c3])
            db.commit()
            db.refresh(c1)
            db.refresh(c2)
            db.refresh(c3)

            # 3. 种子情绪胶囊小品
            capsule1 = EmotionCapsule(
                worldview_id=wv1.id,
                character_id=c1.id,
                title="凌晨三点的雨与未拆封的记忆信件",
                slug="rain-at-3am-and-unopened-letters",
                cover_image="https://images.unsplash.com/photo-1515694346937-94d85e41e6f0?q=80&w=800&auto=format&fit=crop",
                summary="新安托利亚的雨总是带着微弱的金属酸味。雷文推开旧仓库的门，一封泛黄的信件静静躺在货架角落...",
                content_md="""### 凌晨三点的雨与未拆封的记忆信件

新安托利亚的雨总是带着微弱的金属酸味。雨滴撞击在生锈的霓虹灯牌上，发出噼啪的微弱声响。

雷文推开地下三十层旧仓库的卷帘门，幽蓝色的义眼在黑暗中微微聚焦。货架角落里，一只密封在晶体树脂中的信封正散发着极淡的暖黄色荧光——那是一段没有被中央记忆库归档的「原始情绪残留」。

「现在的年轻人，连告别都要用加密信道一键抹除了。」雷文低声自语，戴上防静电手套，小心翼翼地托起那枚晶体。

晶体接触到手套上传感器的瞬间，一段微弱的声音震颤直接传入他的听觉神经：
*“如果有一天我忘记了春天草地的味道，请帮我把这首歌放给第七街区的老槐树听……”*

在这个所有情绪都被明码标价、所有痛苦都被药物抹平的时代，居然还有人愿意为了一棵快要枯死的老树保留一份眷恋。

雷文没有将这枚晶体上传到回收站，而是轻轻拉开自己风衣内侧的口袋，将它放在了离心口最近的地方。

「至少在这个雨夜，这份记忆还没过期。」他拉紧兜帽，转身走入了漫天雨幕之中。""",
                word_count=860,
                mood_tag="治愈",
                mood_color="BLUE",
                reading_time_mins=3,
                view_count=128,
                like_count=42,
                is_featured=1,
                is_published=1
            )

            capsule2 = EmotionCapsule(
                worldview_id=wv1.id,
                character_id=c2.id,
                title="温室里的最后一片发光叶子",
                slug="last-luminescent-leaf-in-greenhouse",
                cover_image="https://images.unsplash.com/photo-1509198397868-475647b2a1e5?q=80&w=800&auto=format&fit=crop",
                summary="露娜莉亚用手指轻轻触碰那片快要凋零的薄荷草。植物的脉络里，正流动着昨夜收集的温暖笑声...",
                content_md="""### 温室里的最后一片发光叶子

浮空温室穹顶外的星尘正在缓慢旋转。露娜莉亚蹲在第三试验区前，指尖轻触着一株低垂的星环夜光草。

「别难过，今天收集到的是一位老水手回忆家乡海风的情绪能量哦。」她轻声细语，仿佛在与一个任性的孩子交谈。

随着她指尖温度的传递，原本暗淡的叶片边缘突然泛起了一圈柔和的金黄色微光。整座温室里，数以百计的发光植物像被唤醒的萤火虫一般，依次亮起了温暖的呼吸律动。

在浮空城的冷酷钢铁架构之下，这间不起眼的玻璃温室就像是一颗跳动着的绿色心脏。每一个来到这里的旅人，都能在空气中闻到属于自己童年的泥土芳香。

露娜莉亚摘下一片最亮的发光叶子，将它夹进透明的小玻璃管里，系上一根纤细的银丝线。

「送给今天感到疲惫的每一个人，愿你们的梦境里都有温暖的光。」她微笑着对着星空举起玻璃管。""",
                word_count=920,
                mood_tag="温暖",
                mood_color="YELLOW",
                reading_time_mins=3,
                view_count=215,
                like_count=89,
                is_featured=1,
                is_published=1
            )
            db.add_all([capsule1, capsule2])

            # 4. 种子 AVG 章节
            avg1 = AvgChapter(
                worldview_id=wv1.id,
                character_id=c1.id,
                chapter_code="demo-ch1-lost-signal",
                chapter_name="第一章：失落的深空信标",
                chapter_no=1,
                cover_image="https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=800&auto=format&fit=crop",
                summary="雷文接收到了来自旧地球轨道的加密呼救信号。在这场短篇互动冒险中，你将扮演雷文做出关键抉择，打捞失落的情绪核心。",
                game_url="/games/demo-avg/index.html",
                playtime_mins=10,
                is_free=1,
                is_published=1,
                sort_order=1
            )
            db.add(avg1)
            db.commit()
            logger.info("Initialized seed data for DreamClip Universe & Characters successfully!")
        
        ensure_seed_banners(db)
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("============================================================")
    logger.info("  %s 启动中...", settings.PROJECT_NAME)
    logger.info("============================================================")
    init_seed_universe_data()
    asyncio.create_task(register_to_base())
    logger.info("  服务端口: \thttp://localhost:%s", settings.SERVER_PORT)
    logger.info("  梦之厅主站: \thttp://localhost:%s/", settings.SERVER_PORT)
    logger.info("  内容工坊: \thttp://localhost:%s/studio", settings.SERVER_PORT)
    logger.info("  Swagger UI: \thttp://localhost:%s/docs", settings.SERVER_PORT)
    logger.info("============================================================")
    yield
    logger.info("DreamClip service shutdown complete.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="DreamClip 梦之厅业务微服务：提供梦之厅公众主站、DreamClip Studio 内容工坊、世界观IP、角色档案、情绪胶囊原创图文及AVG互动剧场。",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载 API V1 路由
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["00.健康检查"])
def health():
    return {"status": "UP", "service": "dreamclip", "platform": "MagicStarPlatform", "code": 200}

# 挂载静态 Web 资源
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

def serve_static_page(filename: str):
    file_path = os.path.join(static_dir, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(static_dir, "universe.html"))

@app.get("/", include_in_schema=False)
def index_page():
    return serve_static_page("universe.html")

@app.get("/universe", include_in_schema=False)
@app.get("/universe/{identifier}", include_in_schema=False)
@app.get("/dreamclip", include_in_schema=False)
def universe_page(identifier: str = None):
    return serve_static_page("universe.html")

@app.get("/studio", include_in_schema=False)
@app.get("/studio/", include_in_schema=False)
@app.get("/admin", include_in_schema=False)
@app.get("/admin/", include_in_schema=False)
def studio_page():
    """DreamClip 主站专属内容工坊与运营中台"""
    return serve_static_page("studio.html")

@app.get("/capsules", include_in_schema=False)
@app.get("/capsule/{identifier}", include_in_schema=False)
def capsule_page(identifier: str = None):
    if not identifier:
        return serve_static_page("universe.html")
    return serve_static_page("capsule.html")

@app.get("/character/{identifier}", include_in_schema=False)
def character_page(identifier: str):
    return serve_static_page("character.html")

@app.get("/games", include_in_schema=False)
def games_page():
    return serve_static_page("games.html")

@app.get("/game/{chapter_code}", include_in_schema=False)
def game_play_page(chapter_code: str):
    return serve_static_page("game_play.html")

# AdSense 4 大必备合规页面
@app.get("/about", include_in_schema=False)
def about_page():
    return serve_static_page("about.html")

@app.get("/privacy", include_in_schema=False)
def privacy_page():
    return serve_static_page("privacy.html")

@app.get("/terms", include_in_schema=False)
def terms_page():
    return serve_static_page("terms.html")

@app.get("/contact", include_in_schema=False)
def contact_page():
    return serve_static_page("contact.html")

# 挂载独立的 H5 游戏静态目录
games_dir = os.path.join(static_dir, "games")
if not os.path.exists(games_dir):
    os.makedirs(games_dir, exist_ok=True)
app.mount("/games", StaticFiles(directory=games_dir), name="games")
