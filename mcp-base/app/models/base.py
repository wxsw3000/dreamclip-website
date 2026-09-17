from datetime import datetime
from sqlalchemy import Column, BigInteger, Integer, DateTime, SmallInteger, String
from app.core.database import Base

class BaseModel(Base):
    """抽象基类：通用自增主键与审计时间戳"""
    __abstract__ = True
    
    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="物理主键ID")
    is_deleted = Column(SmallInteger, default=0, nullable=False, comment="逻辑删除标记 (0-正常, 1-删除)")
    created_by = Column(String(64), nullable=True, comment="创建人")
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    updated_by = Column(String(64), nullable=True, comment="更新人")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")
