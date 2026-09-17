from sqlalchemy import Column, String, Integer, SmallInteger, BigInteger, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.core.database import Base

# 用户-角色 多对多关联表
sys_user_role = Table(
    "sys_user_role",
    Base.metadata,
    Column("user_id", BigInteger().with_variant(Integer, "sqlite"), ForeignKey("sys_user.id"), primary_key=True),
    Column("role_id", BigInteger().with_variant(Integer, "sqlite"), ForeignKey("sys_role.id"), primary_key=True)
)

# 角色-菜单 多对多关联表
sys_role_menu = Table(
    "sys_role_menu",
    Base.metadata,
    Column("role_id", BigInteger().with_variant(Integer, "sqlite"), ForeignKey("sys_role.id"), primary_key=True),
    Column("menu_id", BigInteger().with_variant(Integer, "sqlite"), ForeignKey("sys_menu.id"), primary_key=True)
)

class SysUser(BaseModel):
    """系统用户表 (包含内置 superadmin)"""
    __tablename__ = "sys_user"
    
    username = Column(String(64), unique=True, nullable=False, index=True, comment="登录用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    real_name = Column(String(64), nullable=False, comment="真实姓名/昵称")
    email = Column(String(128), nullable=True, comment="邮箱")
    phone = Column(String(32), nullable=True, comment="手机号")
    avatar = Column(String(255), nullable=True, comment="头像URL")
    personality_color = Column(String(32), default="BLUE", nullable=True, comment="性格色彩 (RED-烈焰开拓, BLUE-静谧理性, YELLOW-璀璨治愈, GREEN-深林共情)")
    zodiac = Column(String(32), nullable=True, comment="星座 (如 白羊座, 金牛座, 双子座等)")
    unlocked_data = Column(Text, nullable=True, comment="已解锁章节、阅读历史与成就 (JSON)")
    is_superadmin = Column(SmallInteger, default=0, nullable=False, comment="是否超级管理员 (1-是, 0-否)")
    tenant_code = Column(String(32), default="SYSTEM", nullable=False, comment="所属租户编码")
    status = Column(String(16), default="ACTIVE", nullable=False, comment="状态 (ACTIVE-正常, DISABLED-禁用)")
    remark = Column(String(255), nullable=True, comment="备注")

    roles = relationship("SysRole", secondary=sys_user_role, back_populates="users", lazy="joined")

class SysRole(BaseModel):
    """系统角色表"""
    __tablename__ = "sys_role"
    
    role_code = Column(String(64), unique=True, nullable=False, index=True, comment="角色编码")
    role_name = Column(String(64), nullable=False, comment="角色名称")
    role_level = Column(Integer, default=10, comment="角色等级 (1-超管, 5-租户管理员, 10-普通操作员)")
    status = Column(String(16), default="ACTIVE", nullable=False, comment="状态")
    remark = Column(String(255), nullable=True, comment="角色说明")

    users = relationship("SysUser", secondary=sys_user_role, back_populates="roles")
    menus = relationship("SysMenu", secondary=sys_role_menu, lazy="joined")

class SysMenu(BaseModel):
    """系统菜单与权限点表 (动态树形菜单与路由)"""
    __tablename__ = "sys_menu"
    
    parent_id = Column(BigInteger().with_variant(Integer, "sqlite"), default=0, nullable=False, comment="父级菜单ID (0为根菜单)")
    menu_name = Column(String(64), nullable=False, comment="菜单名称")
    menu_type = Column(String(16), default="MENU", nullable=False, comment="类型 (DIR-目录, MENU-菜单, BUTTON-按钮, LINK-外部微服务链接)")
    path = Column(String(128), nullable=True, comment="前端路由地址或页面路径")
    component = Column(String(128), nullable=True, comment="前端组件标识")
    icon = Column(String(64), nullable=True, comment="图标类名")
    permission = Column(String(128), nullable=True, comment="权限标识 (如 sys:user:list)")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序序号")
    is_visible = Column(SmallInteger, default=1, nullable=False, comment="是否显示 (1-显示, 0-隐藏)")
    service_code = Column(String(64), nullable=True, comment="所属微服务编码 (为空则为底座原生)")
