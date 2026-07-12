import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.user import UserSignup, UserLogin, UserResponse

router = APIRouter()

@router.post("/signup", response_model=UserResponse)
def signup(
    user_in: UserSignup,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Register a new user as an Employee.
    """
    user = db.query(User).filter(User.email == user_in.email.lower()).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    
    new_user_id = "e_" + uuid.uuid4().hex[:8]
    new_user = User(
        id=new_user_id,
        name=user_in.name,
        email=user_in.email.lower(),
        hashed_password=security.get_password_hash(user_in.password),
        role="employee",
        department_id=user_in.department_id,
        status="active"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=UserResponse)
def login(
    response: Response,
    credentials: UserLogin,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Authenticate user, issue JWT token, set HTTPOnly cookie, and return User.
    """
    user = db.query(User).filter(User.email == credentials.email.lower()).first()
    if not user or not security.verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Incorrect email or password"
        )
    if user.status != "active":
        raise HTTPException(
            status_code=400,
            detail="Inactive user account"
        )
    
    # Generate token
    token = security.create_access_token(subject=user.id)
    
    # Set httpOnly cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=11520 * 60,
        samesite="lax",
        secure=False
    )
    
    # Set headers
    response.headers["Authorization"] = f"Bearer {token}"
    response.headers["X-Access-Token"] = token
    
    return user

@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get current logged in user.
    """
    return current_user

@router.post("/logout")
def logout(response: Response):
    """
    Clear access token cookie.
    """
    response.delete_cookie("access_token")
    return {"detail": "Successfully logged out"}
