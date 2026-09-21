from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class DictTypeOut(BaseModel):
    id: int
    dict_code: str
    dict_name: str
    status: str
    remark: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DictDataOut(BaseModel):
    id: int
    dict_code: str
    data_label: str
    data_value: str
    sort_order: int
    css_class: Optional[str] = None
    status: str
    remark: Optional[str] = None

    class Config:
        from_attributes = True

class ConfigOut(BaseModel):
    id: int
    config_key: str
    config_name: str
    config_value: str
    is_system: int
    remark: Optional[str] = None

    class Config:
        from_attributes = True

class ConfigUpdate(BaseModel):
    config_value: str
    remark: Optional[str] = None
