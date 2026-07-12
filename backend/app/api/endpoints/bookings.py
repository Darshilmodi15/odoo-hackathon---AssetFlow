from typing import List
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api import deps
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingResponse
from app.services.booking import BookingService

router = APIRouter()

@router.get("", response_model=List[BookingResponse])
def get_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    List all resource bookings.
    """
    return BookingService.get_all(db)

@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_in: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Create a new booking with overlap checks.
    """
    return BookingService.create(db, booking_in, current_user)

@router.put("/{id}/cancel", response_model=BookingResponse)
def cancel_booking(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Cancel an active booking.
    """
    return BookingService.cancel(db, id, current_user)

@router.post("/{id}/cancel", response_model=BookingResponse)
def cancel_booking_post(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    return BookingService.cancel(db, id, current_user)
