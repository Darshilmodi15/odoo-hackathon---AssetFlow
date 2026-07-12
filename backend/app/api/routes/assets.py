import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_active_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.asset import AssetCreate, AssetRead, AssetUpdate
from app.services import asset_service

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get("", response_model=list[AssetRead])
def list_assets(db: Session = Depends(get_session), _: User = Depends(get_active_user)):
    return asset_service.list_assets(db)


@router.get("/{asset_id}", response_model=AssetRead)
def get_asset(
    asset_id: uuid.UUID,
    db: Session = Depends(get_session),
    _: User = Depends(get_active_user),
):
    return asset_service.get_asset(db, asset_id)


@router.post("", response_model=AssetRead, status_code=201)
def create_asset(
    payload: AssetCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_active_user),
):
    return asset_service.create_asset(db, payload, current_user)


@router.patch("/{asset_id}", response_model=AssetRead)
def update_asset(
    asset_id: uuid.UUID,
    payload: AssetUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_active_user),
):
    return asset_service.update_asset(db, asset_id, payload, current_user)
