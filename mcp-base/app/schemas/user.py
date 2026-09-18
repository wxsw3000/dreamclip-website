from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class UserBase(BaseModel):
    username: str
    real_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    personality_color: Optional[str] = "BLUE"
    zodiac: Optional[str] = None
    unlocked_data: Optional[str] = None
    tenant_code: str = "SYSTEM"
    is_superadmin: int = 0
    status: str = "ACTIVE"
    remark: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    real_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    personality_color: Optional[str] = None
    zodiac: Optional[str] = None
    unlocked_data: Optional[str] = None
    status: Optional[str] = None
    password: Optional[str] = None
    role_ids: Optional[List[int]] = None
    remark: Optional[str] = None

class RoleSimple(BaseModel):
    id: int
    role_code: str
    role_name: str

class UserOut(UserBase):
    id: int
    created_at: datetime
    roles: List[RoleSimple] = []

    class Config:
        from_attributes = True

class MenuSimple(BaseModel):
    id: int
    menu_name: str
    menu_type: str
    service_code: Optional[str] = None
    permission: Optional[str] = None

class RoleOut(BaseModel):
    id: int
    role_code: str
    role_name: str
    role_level: int
    status: str
    remark: Optional[str] = None
    created_at: datetime
    menus: List[MenuSimple] = []

    class Config:
        from_attributes = True

class RoleCreate(BaseModel):
    role_code: str
    role_name: str
    role_level: int = 10
    status: str = "ACTIVE"
    remark: Optional[str] = None
    menu_ids: Optional[List[int]] = []

class RoleUpdate(BaseModel):
    role_name: Optional[str] = None
    role_level: Optional[int] = None
    status: Optional[str] = None
    remark: Optional[str] = None
    menu_ids: Optional[List[int]] = None

class RoleAssignPermissions(BaseModel):
    menu_ids: List[int]

class MenuOut(BaseModel):
    id: int
    parent_id: int
    menu_name: str
    menu_type: str
    path: Optional[str] = None
    component: Optional[str] = None
    icon: Optional[str] = None
    permission: Optional[str] = None
    sort_order: int
    is_visible: int
    service_code: Optional[str] = None
    children: List["MenuOut"] = []

    class Config:
        from_attributes = True

MenuOut.model_rebuild()
