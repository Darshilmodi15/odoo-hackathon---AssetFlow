from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class UserBase(BaseModel):
    name: str
    email: str
    role: str = "employee"
    status: str = "active"

class UserCreate(UserBase):
    password: str
    department_id: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    department_id: Optional[str] = None

class UserSignup(BaseModel):
    name: str
    email: str
    password: str
    department_id: Optional[str] = Field(None, validation_alias="departmentId", serialization_alias="departmentId")

    model_config = ConfigDict(populate_by_name=True)

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    status: str
    department_id: Optional[str] = Field(None, serialization_alias="departmentId")
    joined_at: datetime = Field(..., serialization_alias="joinedAt")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
