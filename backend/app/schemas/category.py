from typing import Optional
from pydantic import BaseModel, ConfigDict

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: Optional[str] = "active"

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: str

    model_config = ConfigDict(from_attributes=True)
