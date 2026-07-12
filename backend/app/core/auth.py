import uuid
from collections.abc import Callable

from fastapi import Depends, status
from sqlalchemy.orm import Session

from app.core.errors import api_error
from app.db.session import get_session
from app.models.user import User
from app.api.deps import get_current_user

ROLES = {"admin", "asset_manager", "department_head", "employee"}
MANAGEMENT_ROLES = {"admin", "asset_manager", "department_head"}


def get_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.status != "active":
        raise api_error(status.HTTP_403_FORBIDDEN, "Inactive user", "INACTIVE_USER")
    return current_user


def require_roles(*roles: str) -> Callable[[User], User]:
    allowed = set(roles)

    def dependency(current_user: User = Depends(get_active_user)) -> User:
        if current_user.role not in allowed:
            raise api_error(status.HTTP_403_FORBIDDEN, "Not enough permissions", "FORBIDDEN_ROLE")
        return current_user

    return dependency
