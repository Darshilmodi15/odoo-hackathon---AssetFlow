from typing import List
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api import deps
from app.models.user import User
from app.schemas.asset import AssetCreate, AssetUpdate, AssetResponse
from app.services.asset import AssetService

router = APIRouter()

@router.get("", response_model=List[AssetResponse])
def get_assets(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get all assets.
    """
    return AssetService.get_all(db)

@router.get("/{id}", response_model=AssetResponse)
def get_asset_by_id(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get asset by ID.
    """
    return AssetService.get_by_id(db, id)

@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset(
    asset_in: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Create a new asset.
    """
    return AssetService.create(db, asset_in, current_user)

@router.put("/{id}", response_model=AssetResponse)
def update_asset(
    id: uuid.UUID,
    asset_in: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Update an existing asset's details.
    """
    return AssetService.update(db, id, asset_in, current_user)

