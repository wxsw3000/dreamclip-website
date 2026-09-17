import logging
import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

logger = logging.getLogger("mcp-universe.database")

def ensure_database_exists():
    """确保 MySQL 目标数据库存在，若不存在则自动创建"""
    try:
        conn = pymysql.connect(
            host=settings.MYSQL_HOST,
            port=int(settings.MYSQL_PORT),
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            charset="utf8mb4",
            connect_timeout=5
        )
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{settings.MYSQL_DB}` "
                f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
        conn.commit()
        conn.close()
        logger.info("Successfully checked/created MySQL database: %s", settings.MYSQL_DB)
    except Exception as e:
        logger.warning("Could not auto-create MySQL database '%s': %s", settings.MYSQL_DB, e)

# 1. 自动建库
ensure_database_exists()

# 2. 初始化 MySQL 引擎
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
    logger.error("Failed to connect to MySQL (%s), falling back to SQLite for safety", e)
    engine = create_engine(
        "sqlite:///./dreamclip_universe.db",
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
