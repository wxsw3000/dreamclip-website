from typing import Optional, List
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    """登录请求参数"""
    username: str = Field(description="用户名", example="superadmin")
    password: str = Field(description="密码", example="123456")

class RegisterRequest(BaseModel):
    """公开注册请求参数"""
    username: str = Field(description="登录用户名", example="dreamer_01")
    password: str = Field(description="登录密码", example="123456")
    real_name: Optional[str] = Field(default=None, description="昵称/姓名", example="星空漫游者")
    email: Optional[str] = Field(default=None, description="邮箱")
    personality_color: Optional[str] = Field(default="BLUE", description="性格色彩 (RED/BLUE/YELLOW/GREEN)", example="BLUE")
    zodiac: Optional[str] = Field(default="天秤座", description="星座", example="天秤座")
    avatar: Optional[str] = Field(default=None, description="头像地址")

class UpdateProfileRequest(BaseModel):
    """用户资料与画像更新"""
    real_name: Optional[str] = None
    email: Optional[str] = None
    personality_color: Optional[str] = None
    zodiac: Optional[str] = None
    avatar: Optional[str] = None
    unlocked_data: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(description="旧密码")
    new_password: str = Field(description="新密码")

class TokenResponse(BaseModel):
    """Token 响应数据"""
    access_token: str = Field(description="JWT Access Token")
    token_type: str = Field(default="Bearer", description="Token 类型")
    expires_in: int = Field(description="有效期(秒)")
    user_info: "UserInfoResponse"

class MyAppItem(BaseModel):
    """当前用户可访问的应用与微服务项"""
    id: str
    service_code: Optional[str] = None
    name: str
    sub: Optional[str] = None
    icon: str = "📱"
    gradient: str = "linear-gradient(135deg, #4f46e5, #06b6d4)"
    url: str
    category: str = "BIZ"
    badge: Optional[str] = None
    is_admin: bool = False
    description: Optional[str] = None
    health_status: str = "HEALTHY"

class UserInfoResponse(BaseModel):
    """当前用户信息与画像载荷"""
    id: int
    username: str
    real_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    personality_color: Optional[str] = "BLUE"
    zodiac: Optional[str] = None
    unlocked_data: Optional[str] = None
    is_superadmin: bool
    roles: List[str] = []
    permissions: List[str] = []

TokenResponse.model_rebuild()
