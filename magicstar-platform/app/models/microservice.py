from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON
from app.models.base import BaseModel

class SysMicroservice(BaseModel):
    """微服务接入注册与健康治理表 (底座承接各种异构微服务的核心)"""
    __tablename__ = "sys_microservice"
    
    service_code = Column(String(64), unique=True, nullable=False, index=True, comment="微服务唯一编码 (如 mcp-mdm, mcp-mes, mcp-algo)")
    service_name = Column(String(128), nullable=False, comment="微服务名称 (如 制造主数据服务, 生产执行调度服务)")
    tech_stack = Column(String(64), default="JAVA", nullable=False, comment="技术栈 (JAVA, PYTHON, GO, NODEJS, DOTNET, OTHER)")
    base_url = Column(String(255), nullable=False, comment="服务基础URL (如 http://127.0.0.1:8080)")
    health_url = Column(String(255), default="/actuator/health", nullable=False, comment="健康检查端点 (如 /actuator/health 或 /health)")
    docs_url = Column(String(255), default="/doc.html", nullable=True, comment="API接口文档地址 (如 /doc.html 或 /docs)")
    gateway_prefix = Column(String(64), nullable=True, comment="网关路由前缀 (如 /service/mdm)")
    category = Column(String(64), default="CORE", nullable=False, comment="服务分类 (BASE, MDM, MES, WMS, QC, DEV, AI, IOT)")
    version = Column(String(32), default="1.0.0", nullable=False, comment="当前版本")
    status = Column(String(16), default="ACTIVE", nullable=False, comment="管理启用状态 (ACTIVE-启用, DISABLED-停用)")
    
    # 动态健康探测指标
    health_status = Column(String(16), default="UNKNOWN", nullable=False, comment="实时健康状态 (HEALTHY-健康在线, UNHEALTHY-异常, DOWN-离线, UNKNOWN-未检测)")
    last_heartbeat = Column(DateTime, nullable=True, comment="最近一次心跳检测时间")
    response_time_ms = Column(Float, default=0.0, comment="最近心跳响应耗时 (毫秒)")
    last_error_msg = Column(String(500), nullable=True, comment="最近一次探测失败原因")
    
    ext_config = Column(JSON, nullable=True, comment="微服务专属扩展配置 (如代理请求头、超时设置等)")
    description = Column(String(500), nullable=True, comment="服务功能描述")
