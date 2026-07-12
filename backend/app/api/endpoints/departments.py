from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.department import DepartmentCreate, DepartmentResponse
from app.services.department import DepartmentService

router = APIRouter()

@router.get("", response_model=List[DepartmentResponse])
def get_departments(db: Session = Depends(get_db)):
    """
    Get all departments.
    """
    return DepartmentService.get_all(db)

@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(dept_in: DepartmentCreate, db: Session = Depends(get_db)):
    """
    Create a new department.
    """
    return DepartmentService.create(db, dept_in)
