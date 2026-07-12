import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    type: str
    title: str
    message: str
    read: bool
    at: datetime
    link: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
