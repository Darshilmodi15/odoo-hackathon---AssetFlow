import uuid

from pydantic import BaseModel, Field, AliasChoices

from app.schemas.user import UserPublic


class SignupRequest(BaseModel):
    name: str = Field(validation_alias=AliasChoices("name", "full_name"), min_length=1, max_length=120)
    email: str
    password: str = Field(min_length=8, max_length=128)
    department_id: uuid.UUID | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
