import uuid
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    code: str = Field(..., min_length=1, max_length=32)
    head_id: Optional[uuid.UUID] = None
    parent_id: Optional[uuid.UUID] = None
    status: Optional[str] = "active"

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    head_id: Optional[uuid.UUID] = None
    parent_id: Optional[uuid.UUID] = None
    status: Optional[str] = None

class DepartmentResponse(DepartmentBase):
    id: uuid.UUID
    status: str

    model_config = ConfigDict(from_attributes=True)
