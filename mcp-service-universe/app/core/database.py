import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

logger = logging.getLogger("mcp-universe.database")

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
        logger.info("Successfully connected to MySQL Database: %s", settings.MYSQL_DB)
except Exception as e:
    logger.warning("Failed to connect to MySQL (%s), falling back to SQLite: dreamclip_universe.db", e)
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
