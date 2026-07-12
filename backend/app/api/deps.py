from typing import Optional
from fastapi import Depends, HTTPException, Security, Request, status
from fastapi.security import APIKeyHeader, APIKeyCookie
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
api_key_cookie = APIKeyCookie(name="access_token", auto_error=False)

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
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
        
    # 3. Check dev bypass header
    if not token:
        dev_user_id = request.headers.get("x-user-id")
        if dev_user_id:
            user = db.query(User).filter(User.id == dev_user_id).first()
            if user:
                return user

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
        
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
        
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
        
    return user

def check_role(allowed_roles: list[str]):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required role: one of {allowed_roles}",
            )
        return current_user
    return dependency
