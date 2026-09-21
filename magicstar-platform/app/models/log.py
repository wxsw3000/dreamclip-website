from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Integer, Text, DateTime
from app.core.database import Base

class SysLoginLog(Base):
    """用户登录审计日志表"""
    __tablename__ = "sys_login_log"
    
    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    username = Column(String(64), nullable=False, index=True, comment="登录用户名")
    login_ip = Column(String(64), nullable=True, comment="登录IP")
    browser = Column(String(128), nullable=True, comment="浏览器")
    os = Column(String(64), nullable=True, comment="操作系统")
    status = Column(String(16), default="SUCCESS", comment="登录状态 (SUCCESS, FAIL)")
    msg = Column(String(255), nullable=True, comment="提示信息")
    login_time = Column(DateTime, default=datetime.now, comment="登录时间")

class SysOperLog(Base):
    """关键操作审计日志表"""
    __tablename__ = "sys_oper_log"
    
    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    title = Column(String(64), nullable=False, comment="操作模块")
    oper_type = Column(String(32), nullable=False, comment="操作类型 (INSERT, UPDATE, DELETE, GRANT, PROBE)")
    method = Column(String(128), nullable=True, comment="请求方法")
    request_url = Column(String(255), nullable=True, comment="请求URL")
    oper_ip = Column(String(64), nullable=True, comment="操作IP")
    oper_username = Column(String(64), nullable=False, comment="操作人")
    status = Column(String(16), default="SUCCESS", comment="操作状态")
    error_msg = Column(Text, nullable=True, comment="错误信息")
    oper_time = Column(DateTime, default=datetime.now, comment="操作时间")
