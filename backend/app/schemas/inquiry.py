import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator

class InquiryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    company: Optional[str] = Field(None, max_length=120)
    message: str = Field(..., min_length=1)

    @field_validator("name", "message")
    @classmethod
    def strip_and_require(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("field must not be blank")
        return v

    @field_validator("company")
    @classmethod
    def strip_company(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

class InquiryResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    company: Optional[str] = None
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
