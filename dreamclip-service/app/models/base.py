from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, DateTime, SmallInteger
from app.core.database import Base

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    is_deleted = Column(SmallInteger, default=0, nullable=False, comment="逻辑删除 (0-未删除, 1-已删除)")
