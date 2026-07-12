import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = None
    status: Optional[str] = "active"

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: uuid.UUID
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
