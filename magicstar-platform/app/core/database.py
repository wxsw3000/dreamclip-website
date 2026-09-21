import os
import logging
import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

logger = logging.getLogger("magicstar-platform.database")

def ensure_database_exists():
    """确保 MySQL 目标数据库存在，并清理旧版临时库"""
    try:
        conn = pymysql.connect(
            host=settings.MYSQL_HOST,
            port=int(settings.MYSQL_PORT),
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            charset="utf8mb4",
            connect_timeout=3
        )
        with conn.cursor() as cursor:
            # 1. 自动创建全新纯净的通用底座库 magicstar_platform_db
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{settings.MYSQL_DB}` "
                f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
        conn.commit()
        conn.close()
        logger.info("Successfully checked/created MySQL database: %s", settings.MYSQL_DB)
    except Exception as e:
        logger.warning("Could not auto-create MySQL database '%s' (%s), using SQLite fallback", settings.MYSQL_DB, e)

# 1. 自动建库与清理
ensure_database_exists()

# 2. 获取正确的 SQLite 数据库文件绝对路径
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sqlite_path = os.path.join(base_dir, "magicstar_platform.db")

# 3. 初始化数据库引擎
try:
    engine = create_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20,
        echo=False
    )
    with engine.connect() as conn:
        logger.info("Connected to MySQL Database: %s", settings.MYSQL_DB)
except Exception as e:
    logger.info("Using SQLite database at %s (Reason: %s)", sqlite_path, e)
    engine = create_engine(
        f"sqlite:///{sqlite_path}",
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI 依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
