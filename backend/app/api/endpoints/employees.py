from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()

class UpdateRoleRequest(BaseModel):
    role: str

class UpdateStatusRequest(BaseModel):
    status: str

@router.get("", response_model=List[UserResponse])
def read_employees(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve employees (User directory). (All authenticated users can list)
    """
    employees = db.query(User).all()
    return employees

@router.put("/{id}/role", response_model=UserResponse)
def update_employee_role(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
    role_in: UpdateRoleRequest,
    current_user: User = Depends(deps.check_role(["admin"])),
) -> Any:
    """
    Update an employee's role. (Admin only)
    """
    if role_in.role not in ["admin", "asset_manager", "department_head", "employee"]:
        raise HTTPException(status_code=400, detail="Invalid role specified")
        
    employee = db.query(User).filter(User.id == id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    employee.role = role_in.role
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee

@router.put("/{id}/status", response_model=UserResponse)
def update_employee_status(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
    status_in: UpdateStatusRequest,
    current_user: User = Depends(deps.check_role(["admin"])),
) -> Any:
    """
    Update an employee's status. (Admin only)
    """
    if status_in.status not in ["active", "inactive"]:
        raise HTTPException(status_code=400, detail="Invalid status specified")
        
    employee = db.query(User).filter(User.id == id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    employee.status = status_in.status
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee
