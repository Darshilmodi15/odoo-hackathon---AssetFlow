import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AssetCondition = Literal["excellent", "good", "fair", "poor"]
AssetStatus = Literal[
    "available",
    "allocated",
    "reserved",
    "under_maintenance",
    "lost",
    "retired",
    "disposed",
]


class AssetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    category_id: uuid.UUID
    serial_number: str = Field(min_length=1, max_length=120)
    department_id: uuid.UUID | None = None
    location: str = Field(min_length=1, max_length=160)
    condition: AssetCondition = "good"
    shared: bool = False
    acquisition_date: date
    acquisition_cost: Decimal = Decimal("0")
    notes: str | None = None
    status: AssetStatus = "available"


class AssetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    category_id: uuid.UUID | None = None
    serial_number: str | None = Field(default=None, min_length=1, max_length=120)
    department_id: uuid.UUID | None = None
    assigned_to_id: uuid.UUID | None = None
    location: str | None = Field(default=None, min_length=1, max_length=160)
    condition: AssetCondition | None = None
    status: AssetStatus | None = None
    shared: bool | None = None
    acquisition_date: date | None = None
    acquisition_cost: Decimal | None = None
    notes: str | None = None


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tag: str
    name: str
    category_id: uuid.UUID
    serial_number: str
    department_id: uuid.UUID | None
    assigned_to_id: uuid.UUID | None
    location: str
    condition: AssetCondition
    status: AssetStatus
    shared: bool
    acquisition_date: date
    acquisition_cost: Decimal
    notes: str | None
    updated_at: datetime
