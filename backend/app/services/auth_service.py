from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import api_error
from app.core.security import create_access_token, hash_password, verify_password
from app.models.organization import Department
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse


def signup(db: Session, payload: SignupRequest) -> User:
    email = payload.email.lower()
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        raise api_error(status.HTTP_409_CONFLICT, "Email already exists", "EMAIL_ALREADY_EXISTS")
    if payload.department_id and not db.get(Department, payload.department_id):
        raise api_error(status.HTTP_404_NOT_FOUND, "Department not found", "USER_NOT_FOUND")
    user = User(
        name=payload.name,
        email=email,
        hashed_password=hash_password(payload.password),
        role="employee",
        department_id=payload.department_id,
        status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(db: Session, payload: LoginRequest) -> TokenResponse:
    email = payload.email.lower()
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise api_error(status.HTTP_401_UNAUTHORIZED, "Invalid credentials", "INVALID_CREDENTIALS")
    if user.status != "active":
        raise api_error(status.HTTP_403_FORBIDDEN, "Inactive user", "INACTIVE_USER")
    token = create_access_token(str(user.id), user.role)
    return TokenResponse(access_token=token, user=user)
