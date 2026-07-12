from typing import Optional
from pydantic import BaseModel, ConfigDict

class DepartmentBase(BaseModel):
    name: str
    code: str
    head_id: Optional[str] = None
    parent_id: Optional[str] = None
    status: Optional[str] = "active"

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    head_id: Optional[str] = None
    parent_id: Optional[str] = None
    status: Optional[str] = None

class DepartmentResponse(DepartmentBase):
    id: str

    model_config = ConfigDict(from_attributes=True)
