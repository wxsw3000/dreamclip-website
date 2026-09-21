from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class MicroserviceBase(BaseModel):
    service_code: str = Field(description="微服务唯一编码 (如 mcp-mdm, mcp-mes)")
    service_name: str = Field(description="微服务名称")
    base_url: str = Field(description="服务部署基础地址 (如 http://127.0.0.1:8080)")
    health_url: str = Field(default="/health", description="健康检查相对或绝对端点")
    docs_url: Optional[str] = Field(default="/docs", description="API文档地址")
    gateway_prefix: Optional[str] = Field(default=None, description="网关路由前缀")
    tech_stack: Optional[str] = Field(default="SERVICE", description="技术栈 (可选)")
    category: Optional[str] = Field(default="BIZ", description="分类 (可选)")
    version: Optional[str] = Field(default="1.0.0", description="版本号")
    status: Optional[str] = Field(default="ACTIVE", description="启用状态 (ACTIVE/DISABLED)")
    ext_config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None

class MicroserviceCreate(MicroserviceBase):
    pass

class MicroserviceUpdate(BaseModel):
    service_name: Optional[str] = None
    base_url: Optional[str] = None
    health_url: Optional[str] = None
    docs_url: Optional[str] = None
    gateway_prefix: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None

class MicroserviceOut(MicroserviceBase):
    id: int
    health_status: str
    last_heartbeat: Optional[datetime] = None
    response_time_ms: float = 0.0
    last_error_msg: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class HealthProbeResult(BaseModel):
    service_code: str
    service_name: str
    health_status: str
    response_time_ms: float
    status_code: Optional[int] = None
    error_msg: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
