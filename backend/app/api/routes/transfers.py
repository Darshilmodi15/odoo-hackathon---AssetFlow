import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_active_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.workflow import TransferCreate, TransferRead, TransferStatusUpdate
from app.services import workflow_service

router = APIRouter(prefix="/transfers", tags=["Transfers"])


@router.get("", response_model=list[TransferRead])
def list_transfers(db: Session = Depends(get_session), current_user: User = Depends(get_active_user)):
    return workflow_service.list_transfers(db, current_user)


@router.get("/{transfer_id}", response_model=TransferRead)
def get_transfer(transfer_id: uuid.UUID, db: Session = Depends(get_session), current_user: User = Depends(get_active_user)):
    return workflow_service.get_transfer(db, transfer_id, current_user)


@router.post("", response_model=TransferRead, status_code=201)
def create_transfer(payload: TransferCreate, db: Session = Depends(get_session), current_user: User = Depends(get_active_user)):
    return workflow_service.create_transfer(db, payload, current_user)


@router.patch("/{transfer_id}/status", response_model=TransferRead)
def update_transfer_status(transfer_id: uuid.UUID, payload: TransferStatusUpdate, db: Session = Depends(get_session), current_user: User = Depends(get_active_user)):
    return workflow_service.update_transfer_status(db, transfer_id, payload.status, current_user)


@router.put("/{transfer_id}/status", response_model=TransferRead)
def put_transfer_status(transfer_id: uuid.UUID, payload: TransferStatusUpdate, db: Session = Depends(get_session), current_user: User = Depends(get_active_user)):
    return workflow_service.update_transfer_status(db, transfer_id, payload.status, current_user)
