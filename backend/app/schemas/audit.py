import uuid
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class FindingUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=20)  # "pending", "verified", "missing", "damaged"
    notes: Optional[str] = None

class AssignmentCreate(BaseModel):
    auditor_id: uuid.UUID

class FindingCreate(BaseModel):
    asset_id: uuid.UUID
    status: str = "pending"
    notes: Optional[str] = None

class AssignmentResponse(BaseModel):
    id: uuid.UUID
    audit_cycle_id: uuid.UUID
    auditor_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

class FindingResponse(BaseModel):
    id: uuid.UUID
    audit_cycle_id: uuid.UUID
    asset_id: uuid.UUID
    status: str
    notes: Optional[str] = None
    auditor_id: Optional[uuid.UUID] = None
    verified_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class AuditCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    scope_department_id: Optional[uuid.UUID] = None
    scope_location: Optional[str] = None
    start_date: date
    end_date: date
    auditor_ids: List[uuid.UUID]
    asset_ids: List[uuid.UUID]

class AuditResponse(BaseModel):
    id: uuid.UUID
    title: str
    scope_department_id: Optional[uuid.UUID] = None
    scope_location: Optional[str] = None
    start_date: date
    end_date: date
    status: str
    notes: Optional[str] = None
    assignments: List[AssignmentResponse] = []
    findings: List[FindingResponse] = []

    model_config = ConfigDict(from_attributes=True)
