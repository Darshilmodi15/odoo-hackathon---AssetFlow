import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

AllocationStatus = Literal["active", "returned", "transferred", "overdue"]
TransferStatus = Literal["requested", "approved", "rejected", "completed"]
BookingStatus = Literal["upcoming", "ongoing", "completed", "cancelled"]


class AllocationCreate(BaseModel):
    asset_id: uuid.UUID
    employee_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None
    allocation_date: datetime | None = None
    expected_return_at: datetime | None = None
    expected_return_date: datetime | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_target(self):
        if not self.employee_id and not self.department_id:
            raise ValueError("employee_id or department_id is required")
        return self


class AllocationReturn(BaseModel):
    return_date: datetime | None = None
    condition_at_return: str = Field(max_length=32)
    condition_notes: str | None = None
    document_url: str | None = None


class AllocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    asset_id: uuid.UUID
    employee_id: uuid.UUID | None
    department_id: uuid.UUID | None
    allocated_at: datetime
    expected_return_at: datetime | None
    returned_at: datetime | None
    return_condition: str | None
    return_notes: str | None
    return_document_url: str | None
    status: AllocationStatus
    notes: str | None


class TransferCreate(BaseModel):
    asset_id: uuid.UUID
    requested_to_user_id: uuid.UUID | None = None
    requested_to_department_id: uuid.UUID | None = None
    to_employee_id: uuid.UUID | None = None
    to_department_id: uuid.UUID | None = None
    reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_target(self):
        if not (self.requested_to_user_id or self.requested_to_department_id or self.to_employee_id or self.to_department_id):
            raise ValueError("requested target is required")
        return self


class TransferStatusUpdate(BaseModel):
    status: Literal["approved", "rejected"]


class TransferRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    asset_id: uuid.UUID
    from_employee_id: uuid.UUID | None
    from_department_id: uuid.UUID | None
    to_employee_id: uuid.UUID | None
    to_department_id: uuid.UUID | None
    reason: str
    requested_by_id: uuid.UUID
    requested_at: datetime
    approver_id: uuid.UUID | None
    decided_at: datetime | None
    status: TransferStatus


class BookingCreate(BaseModel):
    asset_id: uuid.UUID | None = None
    resource_id: uuid.UUID | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    purpose: str = Field(min_length=1, max_length=255)
    department_id: uuid.UUID | None = None
    attendees: int | None = Field(default=None, ge=1)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_booking(self):
        asset_id = self.asset_id or self.resource_id
        start = self.start_at or self.start_time
        end = self.end_at or self.end_time
        if not asset_id:
            raise ValueError("asset_id or resource_id is required")
        if not start or not end:
            raise ValueError("start and end times are required")
        if end <= start:
            raise ValueError("end_time must be later than start_time")
        return self


class BookingUpdate(BaseModel):
    start_at: datetime | None = None
    end_at: datetime | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    purpose: str | None = Field(default=None, min_length=1, max_length=255)
    department_id: uuid.UUID | None = None
    attendees: int | None = Field(default=None, ge=1)
    notes: str | None = None
    status: BookingStatus | None = None


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    asset_id: uuid.UUID
    booked_by_id: uuid.UUID
    department_id: uuid.UUID | None
    start_at: datetime
    end_at: datetime
    purpose: str
    attendees: int | None
    notes: str | None
    status: BookingStatus
