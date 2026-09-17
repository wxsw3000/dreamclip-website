import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

logger = logging.getLogger("mcp-base.database")

# 尝试连接 MySQL
try:
    engine = create_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20,
        echo=False
    )
    # 测试连接
    with engine.connect() as conn:
        logger.info("Successfully connected to MySQL Database: %s", settings.MYSQL_DB)
except Exception as e:
    logger.warning("Failed to connect to MySQL (%s), falling back to SQLite: mcp_base.db", e)
    engine = create_engine(
        "sqlite:///./mcp_base.db",
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
