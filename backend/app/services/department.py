"""Department service – business logic and database operations.

Routes are responsible for HTTP only; all queries live here.
"""
import uuid
from typing import Optional

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy import or_

from app.core import errors
from app.models.organization import Department
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentStatusPatch


class DepartmentService:
    # ── List ─────────────────────────────────────────────────────────────────

    @staticmethod
    def get_list(
        db: Session,
        *,
        search: Optional[str] = None,
        status: Optional[str] = None,
        parent_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "name",
        order: str = "asc",
    ):
        q = db.query(Department)

        if search:
            pattern = f"%{search}%"
            q = q.filter(
                or_(
                    Department.name.ilike(pattern),
                    Department.code.ilike(pattern),
                )
            )
        if status:
            q = q.filter(Department.status == status)
        if parent_id is not None:
            q = q.filter(Department.parent_id == parent_id)

        # Sorting
        sort_col = getattr(Department, sort_by, Department.name)
        if order.lower() == "desc":
            sort_col = sort_col.desc()
        q = q.order_by(sort_col)

        total = q.count()
        items = q.offset(skip).limit(limit).all()
        return items, total

    # ── Read one ─────────────────────────────────────────────────────────────

    @staticmethod
    def get_by_id(db: Session, department_id: uuid.UUID) -> Department:
        dept = db.query(Department).filter(Department.id == department_id).first()
        if not dept:
            errors.department_not_found()
        return dept  # type: ignore[return-value]

    # ── Create ────────────────────────────────────────────────────────────────

    @staticmethod
    def create(db: Session, dept_in: DepartmentCreate) -> Department:
        # Unique code check
        if db.query(Department).filter(Department.code == dept_in.code).first():
            errors.department_code_conflict()

        # Unique name check
        if db.query(Department).filter(Department.name == dept_in.name).first():
            errors.department_name_conflict()

        # Parent must exist and must not be itself (can't self-reference on create)
        if dept_in.parent_id:
            if not db.query(Department).filter(Department.id == dept_in.parent_id).first():
                errors.invalid_parent_department("Parent department does not exist")

        # Head must exist
        if dept_in.head_id:
            if not db.query(User).filter(User.id == dept_in.head_id).first():
                errors.bad_request("Department head user does not exist", "INVALID_HEAD_USER")

        db_obj = Department(
            name=dept_in.name,
            code=dept_in.code,
            head_id=dept_in.head_id,
            parent_id=dept_in.parent_id,
            status=dept_in.status or "active",
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # ── Update ────────────────────────────────────────────────────────────────

    @staticmethod
    def update(
        db: Session, department_id: uuid.UUID, dept_in: DepartmentUpdate
    ) -> Department:
        dept = DepartmentService.get_by_id(db, department_id)
        update_data = dept_in.model_dump(exclude_unset=True)

        if "code" in update_data and update_data["code"] != dept.code:
            if db.query(Department).filter(Department.code == update_data["code"]).first():
                errors.department_code_conflict()

        if "name" in update_data and update_data["name"] != dept.name:
            if db.query(Department).filter(Department.name == update_data["name"]).first():
                errors.department_name_conflict()

        if "parent_id" in update_data and update_data["parent_id"]:
            if update_data["parent_id"] == department_id:
                errors.invalid_parent_department(
                    "A department cannot be its own parent"
                )
            if not db.query(Department).filter(
                Department.id == update_data["parent_id"]
            ).first():
                errors.invalid_parent_department("Parent department does not exist")

        if "head_id" in update_data and update_data["head_id"]:
            if not db.query(User).filter(User.id == update_data["head_id"]).first():
                errors.bad_request("Department head user does not exist", "INVALID_HEAD_USER")

        for field, value in update_data.items():
            setattr(dept, field, value)

        db.commit()
        db.refresh(dept)
        return dept

    # ── Status patch ──────────────────────────────────────────────────────────

    @staticmethod
    def patch_status(
        db: Session, department_id: uuid.UUID, patch: DepartmentStatusPatch
    ) -> Department:
        dept = DepartmentService.get_by_id(db, department_id)
        dept.status = patch.status
        db.commit()
        db.refresh(dept)
        return dept
