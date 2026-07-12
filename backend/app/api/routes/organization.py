import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.db.session import get_session
from app.models.user import User
from app.schemas.organization import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    DepartmentCreate,
    DepartmentRead,
    DepartmentUpdate,
)
from app.services import organization_service

router = APIRouter(tags=["Organization"])


@router.get("/departments", response_model=list[DepartmentRead])
def list_departments(db: Session = Depends(get_session)):
    return organization_service.list_departments(db)


@router.post("/departments", response_model=DepartmentRead, status_code=201)
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_session),
    _: User = Depends(require_roles("admin")),
):
    return organization_service.create_department(db, payload)


@router.patch("/departments/{department_id}", response_model=DepartmentRead)
def update_department(
    department_id: uuid.UUID,
    payload: DepartmentUpdate,
    db: Session = Depends(get_session),
    _: User = Depends(require_roles("admin")),
):
    return organization_service.update_department(db, department_id, payload)


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_session)):
    return organization_service.list_categories(db)


@router.post("/categories", response_model=CategoryRead, status_code=201)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_session),
    _: User = Depends(require_roles("admin", "asset_manager")),
):
    return organization_service.create_category(db, payload)


@router.patch("/categories/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    db: Session = Depends(get_session),
    _: User = Depends(require_roles("admin", "asset_manager")),
):
    return organization_service.update_category(db, category_id, payload)
