import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "DreamClip 核心服务底座 (DreamClip-Base)"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # 服务器端口
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    
    # 数据库配置 (优先连接 MySQL dreamclip_base_db，失败自动回退 sqlite)
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "19870404")
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT: str = os.getenv("MYSQL_PORT", "3306")
    MYSQL_DB: str = os.getenv("MYSQL_DB", "dreamclip_base_db")
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"

    # JWT 安全认证配置
    SECRET_KEY: str = "dreamclip-universe-superadmin-secret-key-2026-secure"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天有效期
    
    # 预制 SuperAdmin 超级管理员初始凭据
    SUPERADMIN_USERNAME: str = "superadmin"
    SUPERADMIN_DEFAULT_PASSWORD: str = "123456"
    SUPERADMIN_REAL_NAME: str = "DreamClip 平台超管"
    SUPERADMIN_EMAIL: str = "admin@dreamclip.cn"

    # 微服务健康心跳探测间隔 (秒)
    HEALTH_CHECK_INTERVAL_SECONDS: int = 20

    # 跨域配置
    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        case_sensitive = True

settings = Settings()
