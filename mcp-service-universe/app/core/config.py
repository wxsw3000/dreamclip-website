import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "角色宇宙与内容微服务 (Universe-Service)"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8081
    
    # 基础底座服务地址 (用于自注册)
    BASE_SERVICE_URL: str = os.getenv("BASE_SERVICE_URL", "http://127.0.0.1:8000")
    
    # 本地数据库配置 (优先 MySQL mcp_universe_db，失败自动回退 sqlite)
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "19870404")
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT: str = os.getenv("MYSQL_PORT", "3306")
    MYSQL_DB: str = os.getenv("MYSQL_DB", "mcp_universe_db")
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"

    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        case_sensitive = True

settings = Settings()
