import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class BookingCreate(BaseModel):
    asset_id: uuid.UUID
    start_at: datetime
    end_at: datetime
    purpose: str = Field(..., min_length=1, max_length=255)
    attendees: Optional[int] = None
    notes: Optional[str] = None

class BookingResponse(BaseModel):
    id: uuid.UUID
    asset_id: uuid.UUID
    booked_by_id: uuid.UUID
    department_id: Optional[uuid.UUID] = None
    start_at: datetime
    end_at: datetime
    purpose: str
    attendees: Optional[int] = None
    notes: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)
