from typing import List
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api import deps
from app.models.user import User
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate, MaintenanceResponse
from app.services.maintenance import MaintenanceService

router = APIRouter()

@router.get("", response_model=List[MaintenanceResponse])
def get_maintenance_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    List all maintenance requests.
    """
    return MaintenanceService.get_all(db)

@router.post("", response_model=MaintenanceResponse, status_code=status.HTTP_201_CREATED)
def create_maintenance_request(
    maint_in: MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Raise a new maintenance ticket.
    """
    return MaintenanceService.create(db, maint_in, current_user)

@router.put("/{id}/status", response_model=MaintenanceResponse)
def update_maintenance_status(
    id: uuid.UUID,
    update_in: MaintenanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Update status/assignment/costs for a maintenance request.
    """
    return MaintenanceService.update_status(db, id, update_in, current_user)

@router.put("/{id}", response_model=MaintenanceResponse)
def update_maintenance_status_direct(
    id: uuid.UUID,
    update_in: MaintenanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    return MaintenanceService.update_status(db, id, update_in, current_user)
