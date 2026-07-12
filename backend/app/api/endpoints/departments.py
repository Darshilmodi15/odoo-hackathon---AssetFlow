from typing import List
import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.db.session import get_session
from app.models.user import User
from app.models.organization import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from app.services.department import DepartmentService

router = APIRouter()

@router.get("", response_model=List[DepartmentResponse])
def read_departments(
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Retrieve departments.
    """
    return DepartmentService.get_all(db)

@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    department_in: DepartmentCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.check_role(["admin", "asset_manager"])),
):
    """
    Create new department.
    """
    return DepartmentService.create(db, department_in)

@router.put("/{id}", response_model=DepartmentResponse)
def update_department(
    id: uuid.UUID,
    department_in: DepartmentUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.check_role(["admin", "asset_manager"])),
):
    """
    Update a department.
    """
    department = db.query(Department).filter(Department.id == id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
        
    update_data = department_in.model_dump(exclude_unset=True)
    
    # Check parent_id if provided
    if "parent_id" in update_data and update_data["parent_id"]:
        if update_data["parent_id"] == id:
            raise HTTPException(status_code=400, detail="A department cannot be its own parent")
        parent = db.query(Department).filter(Department.id == update_data["parent_id"]).first()
        if not parent:
            raise HTTPException(status_code=400, detail="Parent department not found")

    # Check head_id if provided
    if "head_id" in update_data and update_data["head_id"]:
        head = db.query(User).filter(User.id == update_data["head_id"]).first()
        if not head:
            raise HTTPException(status_code=400, detail="Department head user not found")

    for field in update_data:
        setattr(department, field, update_data[field])
        
    db.commit()
    db.refresh(department)
    return department
