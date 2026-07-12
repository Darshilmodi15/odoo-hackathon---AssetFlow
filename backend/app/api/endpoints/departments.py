import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.department import Department
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse

router = APIRouter()

@router.get("", response_model=List[DepartmentResponse])
def read_departments(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve departments. (All authenticated users can list)
    """
    departments = db.query(Department).all()
    return departments

@router.post("", response_model=DepartmentResponse)
def create_department(
    *,
    db: Session = Depends(deps.get_db),
    department_in: DepartmentCreate,
    current_user: User = Depends(deps.check_role(["admin"])),
) -> Any:
    """
    Create new department. (Admin only)
    """
    department = db.query(Department).filter(Department.name == department_in.name).first()
    if department:
        raise HTTPException(
            status_code=400,
            detail="The department with this name already exists.",
        )
    
    # Check parent_id if provided
    if department_in.parent_id:
        parent = db.query(Department).filter(Department.id == department_in.parent_id).first()
        if not parent:
            raise HTTPException(status_code=400, detail="Parent department not found")

    # Check head_id if provided
    if department_in.head_id:
        head = db.query(User).filter(User.id == department_in.head_id).first()
        if not head:
            raise HTTPException(status_code=400, detail="Department head user not found")
            
    new_dept_id = "d_" + uuid.uuid4().hex[:8]
    db_obj = Department(
        id=new_dept_id,
        name=department_in.name,
        code=department_in.code,
        head_id=department_in.head_id,
        parent_id=department_in.parent_id,
        status=department_in.status or "active"
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.put("/{id}", response_model=DepartmentResponse)
def update_department(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
    department_in: DepartmentUpdate,
    current_user: User = Depends(deps.check_role(["admin"])),
) -> Any:
    """
    Update a department. (Admin only)
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
        
    db.add(department)
    db.commit()
    db.refresh(department)
    return department
