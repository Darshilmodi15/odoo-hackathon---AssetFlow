from typing import List
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api import deps
from app.models.user import User
from app.models.asset import Allocation
from app.schemas.asset import AllocationCreate, AllocationReturn, AllocationResponse
from app.services.asset import AssetService

router = APIRouter()

@router.get("", response_model=List[AllocationResponse])
def get_allocations(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    List all asset allocations.
    """
    return db.query(Allocation).all()

@router.post("", response_model=AllocationResponse, status_code=status.HTTP_201_CREATED)
def create_allocation(
    alloc_in: AllocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Allocate an asset to an employee.
    """
    return AssetService.allocate(db, alloc_in, current_user)

@router.post("/{id}/return", response_model=AllocationResponse)
def return_asset(
    id: uuid.UUID,
    return_in: AllocationReturn,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Return an allocated asset.
    """
    return AssetService.return_asset(db, id, return_in, current_user)
