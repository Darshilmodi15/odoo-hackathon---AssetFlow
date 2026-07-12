import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_active_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.workflow import BookingCreate, BookingRead, BookingUpdate
from app.services import workflow_service

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("", response_model=list[BookingRead])
def list_bookings(db: Session = Depends(get_session), current_user: User = Depends(get_active_user)):
    return workflow_service.list_bookings(db, current_user)


@router.get("/{booking_id}", response_model=BookingRead)
def get_booking(booking_id: uuid.UUID, db: Session = Depends(get_session), current_user: User = Depends(get_active_user)):
    return workflow_service.get_booking(db, booking_id, current_user)


@router.post("", response_model=BookingRead, status_code=201)
def create_booking(payload: BookingCreate, db: Session = Depends(get_session), current_user: User = Depends(get_active_user)):
    return workflow_service.create_booking(db, payload, current_user)


@router.put("/{booking_id}", response_model=BookingRead)
def update_booking(booking_id: uuid.UUID, payload: BookingUpdate, db: Session = Depends(get_session), current_user: User = Depends(get_active_user)):
    return workflow_service.update_booking(db, booking_id, payload, current_user)


@router.delete("/{booking_id}", response_model=BookingRead)
def cancel_booking(booking_id: uuid.UUID, db: Session = Depends(get_session), current_user: User = Depends(get_active_user)):
    return workflow_service.cancel_booking(db, booking_id, current_user)
