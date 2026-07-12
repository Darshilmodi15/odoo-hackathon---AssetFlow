"""Asset category HTTP endpoints – routes only, no business logic."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.db.session import get_session
from app.models.user import User
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryStatusPatch,
    CategoryResponse,
    CategoryListResponse,
)
from app.services.category import CategoryService

router = APIRouter()


@router.get("", response_model=CategoryListResponse)
def list_categories(
    search: Optional[str] = Query(None, description="Search by name"),
    status: Optional[str] = Query(None, description="Filter by status (active/inactive)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    sort_by: str = Query("name", description="Field to sort by"),
    order: str = Query("asc", description="asc or desc"),
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.get_current_user),
):
    """List asset categories with optional filters, pagination, and sorting."""
    items, total = CategoryService.get_list(
        db,
        search=search,
        status=status,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        order=order,
    )
    return CategoryListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.get_current_user),
):
    """Retrieve a single category by ID."""
    return CategoryService.get_by_id(db, category_id)


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.check_role(["admin", "asset_manager"])),
):
    """Create a new asset category."""
    return CategoryService.create(db, category_in)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: uuid.UUID,
    category_in: CategoryUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.check_role(["admin", "asset_manager"])),
):
    """Update an asset category."""
    return CategoryService.update(db, category_id, category_in)


@router.patch("/{category_id}/status", response_model=CategoryResponse)
def patch_category_status(
    category_id: uuid.UUID,
    patch: CategoryStatusPatch,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.check_role(["admin", "asset_manager"])),
):
    """Toggle a category's active/inactive status."""
    return CategoryService.patch_status(db, category_id, patch)
