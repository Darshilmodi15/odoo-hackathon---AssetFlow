import uuid

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import api_error
from app.models.user import User
from app.models.workflow import ActivityLog

VALID_ROLES = {"admin", "asset_manager", "department_head", "employee"}
VALID_STATUSES = {"active", "inactive"}


def list_users(db: Session, current_user: User) -> list[User]:
    stmt = select(User).order_by(User.joined_at.desc())
    if current_user.role == "admin":
        return list(db.scalars(stmt).all())
    if current_user.role == "department_head" and current_user.department_id:
        return list(db.scalars(stmt.where(User.department_id == current_user.department_id)).all())
    raise api_error(status.HTTP_403_FORBIDDEN, "Not enough permissions", "FORBIDDEN_ROLE")


def get_user(db: Session, user_id: uuid.UUID, current_user: User) -> User:
    user = db.get(User, user_id)
    if not user:
        raise api_error(status.HTTP_404_NOT_FOUND, "User not found", "USER_NOT_FOUND")
    if current_user.role == "admin" or current_user.id == user.id:
        return user
    if current_user.role == "department_head" and current_user.department_id == user.department_id:
        return user
    raise api_error(status.HTTP_403_FORBIDDEN, "Not enough permissions", "FORBIDDEN_ROLE")


def _active_admin_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(User).where(User.role == "admin", User.status == "active")) or 0


def update_role(db: Session, user_id: uuid.UUID, role: str, actor: User) -> User:
    if role not in VALID_ROLES:
        raise api_error(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid role", "FORBIDDEN_ROLE")
    user = db.get(User, user_id)
    if not user:
        raise api_error(status.HTTP_404_NOT_FOUND, "User not found", "USER_NOT_FOUND")
    if user.role == "admin" and role != "admin" and user.status == "active" and _active_admin_count(db) <= 1:
        raise api_error(status.HTTP_409_CONFLICT, "Cannot remove the last active admin", "FORBIDDEN_ROLE")
    user.role = role
    db.add(ActivityLog(user_id=actor.id, action="role_update", module="users", entity_id=user.id, description=f"Updated user role to {role}", role=actor.role, status="success"))
    db.commit()
    db.refresh(user)
    return user


def update_status(db: Session, user_id: uuid.UUID, new_status: str, actor: User) -> User:
    if new_status not in VALID_STATUSES:
        raise api_error(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid status", "FORBIDDEN_ROLE")
    user = db.get(User, user_id)
    if not user:
        raise api_error(status.HTTP_404_NOT_FOUND, "User not found", "USER_NOT_FOUND")
    if user.role == "admin" and new_status != "active" and _active_admin_count(db) <= 1:
        raise api_error(status.HTTP_409_CONFLICT, "Cannot deactivate the last active admin", "FORBIDDEN_ROLE")
    user.status = new_status
    db.add(ActivityLog(user_id=actor.id, action="status_update", module="users", entity_id=user.id, description=f"Updated user status to {new_status}", role=actor.role, status="success"))
    db.commit()
    db.refresh(user)
    return user
