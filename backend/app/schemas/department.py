import uuid
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ── Enums (string literals) ───────────────────────────────────────────────────

DEPARTMENT_STATUSES = {"active", "inactive"}


class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    code: str = Field(..., min_length=1, max_length=32)
    head_id: Optional[uuid.UUID] = None
    parent_id: Optional[uuid.UUID] = None
    status: Optional[str] = "active"

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be blank")
        return v

    @field_validator("code")
    @classmethod
    def normalise_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in DEPARTMENT_STATUSES:
            raise ValueError(f"status must be one of {DEPARTMENT_STATUSES}")
        return v


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    code: Optional[str] = Field(None, min_length=1, max_length=32)
    head_id: Optional[uuid.UUID] = None
    parent_id: Optional[uuid.UUID] = None
    status: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("name must not be blank")
        return v

    @field_validator("code")
    @classmethod
    def normalise_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip().upper()
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in DEPARTMENT_STATUSES:
            raise ValueError(f"status must be one of {DEPARTMENT_STATUSES}")
        return v


class DepartmentStatusPatch(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in DEPARTMENT_STATUSES:
            raise ValueError(f"status must be one of {DEPARTMENT_STATUSES}")
        return v


class DepartmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    head_id: Optional[uuid.UUID] = None
    parent_id: Optional[uuid.UUID] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class DepartmentListResponse(BaseModel):
    items: List[DepartmentResponse]
    total: int
    skip: int
    limit: int
