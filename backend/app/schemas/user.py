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
