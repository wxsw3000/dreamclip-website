import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "MagicStar 统一应用门户 (MagicStar Portal)"
    VERSION: str = "1.0.0"
    
    # 门户服务端口
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 3000
    
    # 底座微服务 (mcp-base) 接入地址
    BASE_SERVICE_URL: str = os.getenv("BASE_SERVICE_URL", "http://127.0.0.1:8000")
    
    # 业务微服务 (mcp-service-universe) 接入地址
    UNIVERSE_SERVICE_URL: str = os.getenv("UNIVERSE_SERVICE_URL", "http://127.0.0.1:8081")
    
    # 是否在启动时自动向 base 注册自身
    AUTO_REGISTER_TO_BASE: bool = True
    
    class Config:
        case_sensitive = True

settings = Settings()
