from sqlalchemy import Column, String, Integer, SmallInteger, Text
from app.models.base import BaseModel

class SysDictType(BaseModel):
    """数据字典类型表"""
    __tablename__ = "sys_dict_type"
    
    dict_code = Column(String(64), unique=True, nullable=False, index=True, comment="字典类型编码 (如 industry_type, service_category)")
    dict_name = Column(String(64), nullable=False, comment="字典类型名称")
    status = Column(String(16), default="ACTIVE", nullable=False, comment="状态")
    remark = Column(String(255), nullable=True, comment="备注")

class SysDictData(BaseModel):
    """数据字典数据项表"""
    __tablename__ = "sys_dict_data"
    
    dict_code = Column(String(64), nullable=False, index=True, comment="所属字典类型编码")
    data_label = Column(String(64), nullable=False, comment="字典标签 (如 光学制造)")
    data_value = Column(String(64), nullable=False, comment="字典键值 (如 OPTICAL)")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序序号")
    css_class = Column(String(64), nullable=True, comment="样式属性")
    status = Column(String(16), default="ACTIVE", nullable=False, comment="状态")
    remark = Column(String(255), nullable=True, comment="备注")

class SysConfig(BaseModel):
    """平台全局运行参数表"""
    __tablename__ = "sys_config"
    
    config_key = Column(String(64), unique=True, nullable=False, index=True, comment="参数键名 (如 sys.auth.captcha, sys.tenant.default)")
    config_name = Column(String(64), nullable=False, comment="参数名称")
    config_value = Column(Text, nullable=False, comment="参数键值")
    is_system = Column(SmallInteger, default=1, nullable=False, comment="是否系统内置 (1-是, 0-否)")
    remark = Column(String(255), nullable=True, comment="备注")
