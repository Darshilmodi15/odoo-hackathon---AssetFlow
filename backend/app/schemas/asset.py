import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

# --- ASSET SCHEMAS ---
class AssetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    category_id: uuid.UUID
    serial_number: str = Field(..., min_length=1, max_length=120)
    location: str = Field(..., min_length=1, max_length=120)
    condition: str = Field(..., min_length=1, max_length=20)  # "excellent", "good", "fair", "poor"
    shared: Optional[bool] = False
    acquisition_date: date
    acquisition_cost: Optional[float] = 0.0
    notes: Optional[str] = None

class AssetCreate(AssetBase):
    department_id: Optional[uuid.UUID] = None

class AssetResponse(AssetBase):
    id: uuid.UUID
    tag: str
    department_id: Optional[uuid.UUID] = None
    assigned_to_id: Optional[uuid.UUID] = None
    status: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- ALLOCATION SCHEMAS ---
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


# --- TRANSFER SCHEMAS ---
class TransferCreate(BaseModel):
    asset_id: uuid.UUID
    to_employee_id: uuid.UUID
    reason: str = Field(..., min_length=1)

class TransferStatusUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=20)  # "approved", "rejected"

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
