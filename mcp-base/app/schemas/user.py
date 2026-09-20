from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class UserBase(BaseModel):
    username: str
    real_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    tenant_code: str = "SYSTEM"
    is_superadmin: int = 0
    status: str = "ACTIVE"
    remark: Optional[str] = None

class UserCreate(UserBase):
    password: str
    role_ids: Optional[List[int]] = []

class UserUpdate(BaseModel):
    real_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    status: Optional[str] = None
    password: Optional[str] = None
    role_ids: Optional[List[int]] = None
    remark: Optional[str] = None

class RoleSimple(BaseModel):
    id: int
    role_code: str
    role_name: str

    model_config = ConfigDict(from_attributes=True)

class UserOut(UserBase):
    id: int
    created_at: datetime
    roles: List[RoleSimple] = []

    model_config = ConfigDict(from_attributes=True)

class MenuSimple(BaseModel):
    id: int
    menu_name: str
    menu_type: str
    service_code: Optional[str] = None
    permission: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class RoleOut(BaseModel):
    id: int
    role_code: str
    role_name: str
    role_level: int
    is_system: int = 0
    status: str
    remark: Optional[str] = None
    created_at: datetime
    assigned_apps: List[str] = []
    menus: List[MenuSimple] = []

    model_config = ConfigDict(from_attributes=True)

class RoleCreate(BaseModel):
    role_code: str
    role_name: str
    role_level: int = 10
    status: str = "ACTIVE"
    remark: Optional[str] = None
    service_codes: Optional[List[str]] = []
    menu_ids: Optional[List[int]] = []

class RoleUpdate(BaseModel):
    role_name: Optional[str] = None
    role_level: Optional[int] = None
    status: Optional[str] = None
    remark: Optional[str] = None
    service_codes: Optional[List[str]] = None
    menu_ids: Optional[List[int]] = None

class AppPermissionItem(BaseModel):
    """可供分配的微服务应用条目"""
    id: int
    service_code: str
    service_name: str
    category: Optional[str] = "BIZ"
    tech_stack: Optional[str] = "PYTHON"
    base_url: Optional[str] = ""
    gateway_prefix: Optional[str] = ""
    icon: Optional[str] = "📱"
    description: Optional[str] = ""
    health_status: Optional[str] = "HEALTHY"
    menus: List[MenuSimple] = []

    model_config = ConfigDict(from_attributes=True)

class RoleAssignPermissions(BaseModel):
    """赋予角色应用与菜单权限参数"""
    service_codes: Optional[List[str]] = []
    menu_ids: Optional[List[int]] = []

class RolePermissionOut(BaseModel):
    """角色权限详情与全量应用清单"""
    role_id: int
    role_code: str
    role_name: str
    assigned_service_codes: List[str] = []
    assigned_menu_ids: List[int] = []
    all_apps: List[AppPermissionItem] = []

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

    model_config = ConfigDict(from_attributes=True)

MenuOut.model_rebuild()
