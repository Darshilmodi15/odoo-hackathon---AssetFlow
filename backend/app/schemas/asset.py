import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ── Value sets ────────────────────────────────────────────────────────────────

ASSET_STATUSES = {
    "available", "allocated", "reserved",
    "under_maintenance", "lost", "retired", "disposed",
}
# Statuses that are managed exclusively by workflow services (Darshil's area).
PROTECTED_STATUSES = {"allocated", "reserved", "under_maintenance"}

ASSET_CONDITIONS = {"excellent", "good", "fair", "poor", "damaged"}


# ── Base / Create ─────────────────────────────────────────────────────────────

class AssetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    category_id: uuid.UUID
    serial_number: Optional[str] = Field(None, max_length=120)
    location: str = Field(..., min_length=1, max_length=120)
    condition: str = Field(..., max_length=20)
    shared: Optional[bool] = False
    acquisition_date: date
    acquisition_cost: Optional[float] = Field(default=0.0, ge=0)
    notes: Optional[str] = None

    @field_validator("name", "location")
    @classmethod
    def strip_and_require(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("field must not be blank")
        return v

    @field_validator("serial_number")
    @classmethod
    def strip_serial(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, v: str) -> str:
        if v not in ASSET_CONDITIONS:
            raise ValueError(f"condition must be one of {sorted(ASSET_CONDITIONS)}")
        return v


class AssetCreate(AssetBase):
    department_id: Optional[uuid.UUID] = None
    # tag is auto-generated; do not accept from client


class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    category_id: Optional[uuid.UUID] = None
    serial_number: Optional[str] = Field(None, max_length=120)
    department_id: Optional[uuid.UUID] = None
    location: Optional[str] = Field(None, min_length=1, max_length=120)
    condition: Optional[str] = Field(None, max_length=20)
    shared: Optional[bool] = None
    acquisition_date: Optional[date] = None
    acquisition_cost: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = None
    # status intentionally excluded from generic update – use PATCH /status

    @field_validator("name", "location")
    @classmethod
    def strip_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("field must not be blank")
        return v

    @field_validator("serial_number")
    @classmethod
    def strip_serial(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ASSET_CONDITIONS:
            raise ValueError(f"condition must be one of {sorted(ASSET_CONDITIONS)}")
        return v


class AssetStatusPatch(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ASSET_STATUSES:
            raise ValueError(f"status must be one of {sorted(ASSET_STATUSES)}")
        return v


# ── Response ──────────────────────────────────────────────────────────────────

class AssetResponse(BaseModel):
    id: uuid.UUID
    tag: str
    name: str
    category_id: uuid.UUID
    serial_number: Optional[str] = None
    location: str
    condition: str
    shared: bool
    acquisition_date: date
    acquisition_cost: float
    notes: Optional[str] = None
    department_id: Optional[uuid.UUID] = None
    assigned_to_id: Optional[uuid.UUID] = None
    status: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssetListResponse(BaseModel):
    items: List[AssetResponse]
    total: int
    skip: int
    limit: int


# ── Allocation / Transfer schemas (kept for Darshil's endpoints) ──────────────

class AllocationCreate(BaseModel):
    asset_id: uuid.UUID
    employee_id: uuid.UUID
    expected_return_at: Optional[datetime] = None
    notes: Optional[str] = None


class AllocationReturn(BaseModel):
    return_condition: str = Field(..., min_length=1, max_length=20)
    return_notes: Optional[str] = None


class AllocationResponse(BaseModel):
    id: uuid.UUID
    asset_id: uuid.UUID
    employee_id: uuid.UUID
    department_id: Optional[uuid.UUID] = None
    allocated_at: datetime
    expected_return_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None
    return_condition: Optional[str] = None
    return_notes: Optional[str] = None
    status: str
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TransferCreate(BaseModel):
    asset_id: uuid.UUID
    to_employee_id: uuid.UUID
    reason: str = Field(..., min_length=1)


class TransferStatusUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=20)


class TransferResponse(BaseModel):
    id: uuid.UUID
    code: str
    asset_id: uuid.UUID
    from_employee_id: uuid.UUID
    to_employee_id: uuid.UUID
    reason: str
    requested_by_id: uuid.UUID
    requested_at: datetime
    approver_id: Optional[uuid.UUID] = None
    status: str

    model_config = ConfigDict(from_attributes=True)
