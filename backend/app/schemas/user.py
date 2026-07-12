<<<<<<< HEAD
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
=======
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

UserRole = Literal["admin", "asset_manager", "department_head", "employee"]
UserStatus = Literal["active", "inactive"]


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    role: UserRole
    department_id: uuid.UUID | None = None
    avatar_url: str | None = None
    status: UserStatus
    joined_at: datetime


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    role: UserRole
    department_id: uuid.UUID | None = None
    status: UserStatus


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserStatusUpdate(BaseModel):
    status: UserStatus


class UserListQuery(BaseModel):
    department_id: uuid.UUID | None = Field(default=None)
>>>>>>> 835db53a52e82859b982fe75ce7670b80b1489bd
