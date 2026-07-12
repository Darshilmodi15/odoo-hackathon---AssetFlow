import uuid
from collections.abc import Callable

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import api_error
from app.core.security import decode_access_token
from app.db.session import get_session
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

ROLES = {"admin", "asset_manager", "department_head", "employee"}
MANAGEMENT_ROLES = {"admin", "asset_manager", "department_head"}


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_session),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise api_error(status.HTTP_401_UNAUTHORIZED, "Authentication required", "INVALID_CREDENTIALS")
    payload = decode_access_token(credentials.credentials)
    if not payload or not payload.get("sub"):
        raise api_error(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token", "INVALID_CREDENTIALS")
    try:
        user_id = uuid.UUID(str(payload["sub"]))
    except ValueError:
        raise api_error(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token", "INVALID_CREDENTIALS")
    user = db.get(User, user_id)
    if user is None:
        raise api_error(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token", "INVALID_CREDENTIALS")
    return user


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
