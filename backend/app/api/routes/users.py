import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_active_user, require_roles
from app.db.session import get_session
from app.models.user import User
from app.schemas.user import UserPublic, UserRoleUpdate, UserStatusUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserPublic])
def list_users(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_active_user),
):
    return user_service.list_users(db, current_user)


@router.get("/{user_id}", response_model=UserPublic)
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_active_user),
):
    return user_service.get_user(db, user_id, current_user)


@router.patch("/{user_id}/role", response_model=UserPublic)
def update_role(
    user_id: uuid.UUID,
    payload: UserRoleUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_roles("admin")),
):
    return user_service.update_role(db, user_id, payload.role, current_user)


@router.patch("/{user_id}/status", response_model=UserPublic)
def update_status(
    user_id: uuid.UUID,
    payload: UserStatusUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_roles("admin")),
):
    return user_service.update_status(db, user_id, payload.status, current_user)
