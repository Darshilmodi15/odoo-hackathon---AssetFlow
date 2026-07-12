import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_active_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.workflow import AllocationCreate, AllocationRead, AllocationReturn
from app.services import workflow_service

router = APIRouter(prefix="/allocations", tags=["Allocations"])


@router.get("", response_model=list[AllocationRead])
def list_allocations(
    employee_id: uuid.UUID | None = None,
    asset_id: uuid.UUID | None = None,
    department_id: uuid.UUID | None = None,
    status: str | None = None,
    overdue: bool = Query(default=False),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_active_user),
):
    return workflow_service.list_allocations(db, current_user, employee_id=employee_id, asset_id=asset_id, department_id=department_id, status=status, overdue=overdue)


@router.get("/{allocation_id}", response_model=AllocationRead)
def get_allocation(allocation_id: uuid.UUID, db: Session = Depends(get_session), current_user: User = Depends(get_active_user)):
    return workflow_service.get_allocation(db, allocation_id, current_user)


@router.post("", response_model=AllocationRead, status_code=201)
def create_allocation(payload: AllocationCreate, db: Session = Depends(get_session), current_user: User = Depends(get_active_user)):
    return workflow_service.create_allocation(db, payload, current_user)


@router.post("/{allocation_id}/return", response_model=AllocationRead)
def return_allocation(allocation_id: uuid.UUID, payload: AllocationReturn, db: Session = Depends(get_session), current_user: User = Depends(get_active_user)):
    return workflow_service.return_allocation(db, allocation_id, payload, current_user)
