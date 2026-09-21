from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class TenantBase(BaseModel):
    tenant_code: str = Field(description="企业租户唯一标识，如 KANGLI")
    tenant_name: str = Field(description="企业全称")
    short_name: Optional[str] = None
    industry_type: Optional[str] = "GENERAL"
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    status: str = "ACTIVE"
    expired_at: Optional[datetime] = None
    ext_properties: Optional[Dict[str, Any]] = None
    remark: Optional[str] = None

class TenantCreate(TenantBase):
    pass

class TenantUpdate(BaseModel):
    tenant_name: Optional[str] = None
    short_name: Optional[str] = None
    industry_type: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None
    expired_at: Optional[datetime] = None
    ext_properties: Optional[Dict[str, Any]] = None
    remark: Optional[str] = None

class TenantOut(TenantBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
