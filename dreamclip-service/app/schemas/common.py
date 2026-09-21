from typing import Generic, TypeVar, Optional, Any, List
from pydantic import BaseModel

T = TypeVar("T")

class Result(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None
    timestamp: int = 0

    @classmethod
    def ok(cls, data: Any = None, message: str = "success"):
        import time
        return cls(code=200, message=message, data=data, timestamp=int(time.time() * 1000))

    @classmethod
    def fail(cls, message: str = "fail", code: int = 500, data: Any = None):
        import time
        return cls(code=code, message=message, data=data, timestamp=int(time.time() * 1000))

class PageResult(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
