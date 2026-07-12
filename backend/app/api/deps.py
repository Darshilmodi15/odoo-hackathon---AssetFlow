import uuid
from typing import Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, APIKeyCookie
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.core.security import decode_access_token
from app.models.user import User

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
api_key_cookie = APIKeyCookie(name="access_token", auto_error=False)

def get_current_user(
    db: Session = Depends(get_session),
    authorization: Optional[str] = Security(api_key_header),
    access_token: Optional[str] = Security(api_key_cookie)
) -> User:
    token = None
    
    # 1. Check Authorization Header (Bearer Token)
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ")[1]
    
    # 2. Check Cookie
    if not token and access_token:
        token = access_token

    # 3. JWT Token decoding. Do not silently fall back to a user; protected
    # routes must require a valid active account for the real demo path.
    if token:
        user_id = decode_access_token(token)
        if user_id:
            try:
                user_uuid = uuid.UUID(user_id)
                user = db.query(User).filter(User.id == user_uuid).first()
                if user and user.status == "active":
                    return user
            except ValueError:
                pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )

def check_role(allowed_roles: list[str]):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required role: one of {allowed_roles}",
            )
        return current_user
    return dependency

# Compatibility alias
get_db = get_session

