from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status
from app.models.organization import Department
from app.models.user import User
from app.schemas.department import DepartmentCreate

class DepartmentService:
    @staticmethod
    def get_all(db: Session):
        return db.query(Department).all()

    @staticmethod
    def create(db: Session, dept_in: DepartmentCreate):
        # 1. Check duplicate name or code
        duplicate = db.query(Department).filter(
            or_(
                Department.name == dept_in.name,
                Department.code == dept_in.code
            )
        ).first()
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Department with this name or code already exists."
            )
            
        # 2. Check parent_id exists if specified
        if dept_in.parent_id:
            parent = db.query(Department).filter(Department.id == dept_in.parent_id).first()
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent department does not exist."
                )

        # 3. Check head_id exists if specified
        if dept_in.head_id:
            head = db.query(User).filter(User.id == dept_in.head_id).first()
            if not head:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Department head user does not exist."
                )

        db_obj = Department(
            name=dept_in.name,
            code=dept_in.code,
            head_id=dept_in.head_id,
            parent_id=dept_in.parent_id,
            status=dept_in.status or "active"
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
