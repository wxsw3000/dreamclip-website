from typing import Generic, TypeVar, Optional, Any
from datetime import datetime
import time
from pydantic import BaseModel, Field

T = TypeVar("T")

class Result(BaseModel, Generic[T]):
    """统一 API JSON 响应体"""
    code: int = Field(default=200, description="状态码：200为成功，其余为错误")
    message: str = Field(default="操作成功", description="响应提示信息")
    data: Optional[T] = Field(default=None, description="业务数据载荷")
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000), description="时间戳(毫秒)")

    @classmethod
    def ok(cls, data: Optional[T] = None, message: str = "操作成功") -> "Result[T]":
        return cls(code=200, message=message, data=data)

    @classmethod
    def fail(cls, message: str = "操作失败", code: int = 500, data: Optional[T] = None) -> "Result[T]":
        return cls(code=code, message=message, data=data)

class PageResult(BaseModel, Generic[T]):
    """分页包装响应体"""
    total: int = Field(description="总记录数")
    current: int = Field(description="当前页码")
    size: int = Field(description="每页大小")
    records: list[T] = Field(description="数据列表")
