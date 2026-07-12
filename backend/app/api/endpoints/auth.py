import uuid
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.user import UserSignup, UserLogin, UserResponse
from app.schemas.auth import TokenResponse

router = APIRouter()

def resolve_uuid(val: Optional[str]) -> Optional[uuid.UUID]:
    if not val:
        return None
    val = val.strip()
    if not val or val == "null" or val == "undefined":
        return None
    try:
        return uuid.UUID(val)
    except ValueError:
        # Invalid UUID string — skip instead of generating a fake one
        return None

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
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
            status_code=409,
            detail="The user with this email already exists in the system.",
        )
    
    dept_id = resolve_uuid(user_in.department_id)
    new_user = User(
        id=uuid.uuid4(),
        name=user_in.name,
        email=user_in.email.lower(),
        hashed_password=security.get_password_hash(user_in.password),
        role="employee",
        department_id=dept_id,
        status="active"
    )
    db.add(new_user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Could not create account. Please check the selected department.",
        )
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=TokenResponse)
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
    
    # Set headers for compatibility and return the contract expected by clients.
    response.headers["Authorization"] = f"Bearer {token}"
    response.headers["X-Access-Token"] = token

    return {"access_token": token, "token_type": "bearer", "user": user}

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
