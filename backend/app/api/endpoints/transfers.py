from typing import List
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api import deps
from app.models.user import User
from app.schemas.asset import TransferCreate, TransferStatusUpdate, TransferResponse
from app.services.asset import AssetService

router = APIRouter()

@router.get("", response_model=List[TransferResponse])
def get_transfers(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    List all transfer requests.
    """
    return AssetService.get_transfers(db)

@router.post("", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
def create_transfer(
    transfer_in: TransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Initiate a transfer request.
    """
    return AssetService.create_transfer(db, transfer_in, current_user)

@router.put("/{id}/status", response_model=TransferResponse)
def update_transfer_status(
    id: uuid.UUID,
    status_in: TransferStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Approve or reject a transfer request.
    """
    return AssetService.update_transfer_status(db, id, status_in, current_user)

# Also expose standard PUT /{id} for frontend setStatus call versatility
@router.put("/{id}", response_model=TransferResponse)
def update_transfer_status_direct(
    id: uuid.UUID,
    status_in: TransferStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    return AssetService.update_transfer_status(db, id, status_in, current_user)
