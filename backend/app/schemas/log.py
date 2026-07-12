import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class LogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    action: str
    module: str
    entity_id: Optional[uuid.UUID] = None
    description: str
    role: str
    at: datetime
    status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
