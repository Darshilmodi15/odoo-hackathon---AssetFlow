import uuid

from fastapi import status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import api_error
from app.models.organization import AssetCategory, Department
from app.models.user import User
from app.schemas.organization import CategoryCreate, CategoryUpdate, DepartmentCreate, DepartmentUpdate

VALID_STATUS = {"active", "inactive"}


def list_departments(db: Session) -> list[Department]:
    return list(db.scalars(select(Department).order_by(Department.name)).all())


def create_department(db: Session, payload: DepartmentCreate) -> Department:
    if payload.status not in VALID_STATUS:
        raise api_error(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid status", "INVALID_STATUS")
    if payload.head_id and not db.get(User, payload.head_id):
        raise api_error(status.HTTP_404_NOT_FOUND, "User not found", "USER_NOT_FOUND")
    if payload.parent_id and not db.get(Department, payload.parent_id):
        raise api_error(status.HTTP_404_NOT_FOUND, "Department not found", "DEPARTMENT_NOT_FOUND")
    dep = Department(**payload.model_dump())
    db.add(dep)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise api_error(status.HTTP_409_CONFLICT, "Department code already exists", "DEPARTMENT_CODE_EXISTS")
    db.refresh(dep)
    return dep


def update_department(db: Session, department_id: uuid.UUID, payload: DepartmentUpdate) -> Department:
    dep = db.get(Department, department_id)
    if not dep:
        raise api_error(status.HTTP_404_NOT_FOUND, "Department not found", "DEPARTMENT_NOT_FOUND")
    data = payload.model_dump(exclude_unset=True)
    if data.get("status") and data["status"] not in VALID_STATUS:
        raise api_error(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid status", "INVALID_STATUS")
    for key, value in data.items():
        setattr(dep, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise api_error(status.HTTP_409_CONFLICT, "Department code already exists", "DEPARTMENT_CODE_EXISTS")
    db.refresh(dep)
    return dep


def list_categories(db: Session) -> list[AssetCategory]:
    return list(db.scalars(select(AssetCategory).order_by(AssetCategory.name)).all())


def create_category(db: Session, payload: CategoryCreate) -> AssetCategory:
    if payload.status not in VALID_STATUS:
        raise api_error(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid status", "INVALID_STATUS")
    category = AssetCategory(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category_id: uuid.UUID, payload: CategoryUpdate) -> AssetCategory:
    category = db.get(AssetCategory, category_id)
    if not category:
        raise api_error(status.HTTP_404_NOT_FOUND, "Category not found", "CATEGORY_NOT_FOUND")
    data = payload.model_dump(exclude_unset=True)
    if data.get("status") and data["status"] not in VALID_STATUS:
        raise api_error(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid status", "INVALID_STATUS")
    for key, value in data.items():
        setattr(category, key, value)
    db.commit()
    db.refresh(category)
    return category
