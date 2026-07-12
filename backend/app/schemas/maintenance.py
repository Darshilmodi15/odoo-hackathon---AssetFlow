import uuid
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class MaintenanceHistoryResponse(BaseModel):
    id: uuid.UUID
    status: str
    note: Optional[str] = None
    by_id: uuid.UUID
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MaintenanceCreate(BaseModel):
    asset_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1)
    priority: str = Field(..., min_length=1, max_length=20)  # "low", "medium", "high", "critical"
    preferred_date: Optional[date] = None

class MaintenanceUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=20)
    technician_id: Optional[uuid.UUID] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    resolution_notes: Optional[str] = None
    note: Optional[str] = None  # note for status transition history

class MaintenanceResponse(BaseModel):
    id: uuid.UUID
    code: str
    asset_id: uuid.UUID
    requested_by_id: uuid.UUID
    title: str
    description: str
    priority: str
    status: str
    requested_at: datetime
    preferred_date: Optional[date] = None
    technician_id: Optional[uuid.UUID] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    resolution_notes: Optional[str] = None
    history_entries: List[MaintenanceHistoryResponse] = []

    model_config = ConfigDict(from_attributes=True)
