from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_session
from app.schemas.inquiry import InquiryCreate, InquiryResponse
from app.services.inquiry import InquiryService

router = APIRouter()

@router.post("", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
def create_inquiry(
    inquiry_in: InquiryCreate,
    db: Session = Depends(get_session),
):
    """Submit a new contact/inquiry request."""
    return InquiryService.create(db, inquiry_in)
