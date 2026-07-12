"""Department HTTP endpoints – routes only, no business logic."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.db.session import get_session
from app.models.user import User
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentStatusPatch,
    DepartmentResponse,
    DepartmentListResponse,
)
from app.services.department import DepartmentService

router = APIRouter()


@router.get("", response_model=DepartmentListResponse)
def list_departments(
    search: Optional[str] = Query(None, description="Search by name or code"),
    status: Optional[str] = Query(None, description="Filter by status (active/inactive)"),
    parent_id: Optional[uuid.UUID] = Query(None, description="Filter by parent department"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    sort_by: str = Query("name", description="Field to sort by"),
    order: str = Query("asc", description="asc or desc"),
    db: Session = Depends(get_session),
):
    """List departments with optional filters, pagination, and sorting.

    Public so the signup page can show department choices before login.
    Create/update/status remain role-protected below.
    """
    items, total = DepartmentService.get_list(
        db,
        search=search,
        status=status,
        parent_id=parent_id,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        order=order,
    )
    return DepartmentListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(
    department_id: uuid.UUID,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.get_current_user),
):
    """Retrieve a single department by ID."""
    return DepartmentService.get_by_id(db, department_id)


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    department_in: DepartmentCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.check_role(["admin", "asset_manager"])),
):
    """Create a new department."""
    return DepartmentService.create(db, department_in)


@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: uuid.UUID,
    department_in: DepartmentUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.check_role(["admin", "asset_manager"])),
):
    """Update a department."""
    return DepartmentService.update(db, department_id, department_in)


@router.patch("/{department_id}/status", response_model=DepartmentResponse)
def patch_department_status(
    department_id: uuid.UUID,
    patch: DepartmentStatusPatch,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.check_role(["admin", "asset_manager"])),
):
    """Toggle a department's active/inactive status."""
    return DepartmentService.patch_status(db, department_id, patch)
