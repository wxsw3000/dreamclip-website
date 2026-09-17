from sqlalchemy import Column, String, DateTime, Text, JSON
from app.models.base import BaseModel

class SysTenant(BaseModel):
    """企业租户主档表"""
    __tablename__ = "sys_tenant"
    
    tenant_code = Column(String(32), unique=True, nullable=False, index=True, comment="租户唯一标识 (如 KANGLI, NIGHT_KM)")
    tenant_name = Column(String(128), nullable=False, comment="企业全称")
    short_name = Column(String(64), nullable=True, comment="企业简称")
    industry_type = Column(String(64), nullable=True, comment="行业分类 (OPTICAL, MACHINERY, ELECTRONICS, GENERAL)")
    contact_person = Column(String(64), nullable=True, comment="联系人")
    contact_phone = Column(String(32), nullable=True, comment="联系电话")
    address = Column(String(255), nullable=True, comment="企业地址")
    status = Column(String(16), default="ACTIVE", nullable=False, comment="状态 (ACTIVE-正常, SUSPENDED-暂停, EXPIRED-已到期)")
    expired_at = Column(DateTime, nullable=True, comment="到期时间")
    ext_properties = Column(JSON, nullable=True, comment="租户个性化扩展属性")
    remark = Column(String(500), nullable=True, comment="备注")
