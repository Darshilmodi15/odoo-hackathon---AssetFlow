from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth import get_active_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse
from app.schemas.user import UserPublic, UserRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_session)):
    return auth_service.signup(db, payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_session)):
    return auth_service.login(db, payload)


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_active_user)):
    return current_user
