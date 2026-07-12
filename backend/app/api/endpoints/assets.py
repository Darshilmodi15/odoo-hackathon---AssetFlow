"""Asset HTTP endpoints – routes only, no business logic."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.schemas.asset import (
    AssetCreate,
    AssetUpdate,
    AssetStatusPatch,
    AssetResponse,
    AssetListResponse,
)
from app.services.asset import AssetService

router = APIRouter()


@router.get("", response_model=AssetListResponse)
def list_assets(
    search: Optional[str] = Query(None, description="Search by name, tag, or serial number"),
    tag: Optional[str] = Query(None, description="Filter by asset tag"),
    serial_number: Optional[str] = Query(None, description="Filter by serial number"),
    category_id: Optional[uuid.UUID] = Query(None),
    department_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    condition: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    is_shared: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    sort_by: str = Query("name"),
    order: str = Query("asc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """List assets with rich filtering, pagination, and sorting."""
    items, total = AssetService.get_list(
        db,
        search=search,
        tag=tag,
        serial_number=serial_number,
        category_id=category_id,
        department_id=department_id,
        status=status,
        condition=condition,
        location=location,
        is_shared=is_shared,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        order=order,
    )
    return AssetListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Retrieve a single asset by ID."""
    return AssetService.get_by_id(db, asset_id)


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset(
    asset_in: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.check_role(["admin", "asset_manager"])),
):
    """Register a new asset. Tag is auto-generated."""
    return AssetService.create(db, asset_in, current_user)


@router.put("/{asset_id}", response_model=AssetResponse)
def update_asset(
    asset_id: uuid.UUID,
    asset_in: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.check_role(["admin", "asset_manager"])),
):
    """Update asset details. Status transitions through workflow endpoints only."""
    return AssetService.update(db, asset_id, asset_in, current_user)


@router.patch("/{asset_id}/status", response_model=AssetResponse)
def patch_asset_status(
    asset_id: uuid.UUID,
    patch: AssetStatusPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.check_role(["admin", "asset_manager"])),
):
    """Patch an asset's status. Protected transitions (allocated→available) are guarded."""
    return AssetService.patch_status(db, asset_id, patch, current_user)
