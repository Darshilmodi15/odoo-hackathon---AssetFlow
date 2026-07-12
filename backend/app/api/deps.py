import uuid
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    # 1. Check x-user-id header
    user_id = request.headers.get("x-user-id")
    if user_id:
        try:
            user_uuid = uuid.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
            if user:
                return user
        except ValueError:
            pass
            
    # 2. Try to read first user in DB as dev fallback
    user = db.query(User).first()
    if user:
        return user
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No user found in the database. Please seed users first."
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
