from datetime import datetime, timedelta, timezone
from typing import Any, Union
from jose import JWTError, jwt
from pwdlib import PasswordHash
from app.core.config import settings

password_hash = PasswordHash.recommended()
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def get_password_hash(password: str) -> str:
    return hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return password_hash.verify(plain_password, hashed_password)
    except Exception:
        return False


def create_access_token(
    user_id: Any = None,
    role: str = "employee",
    subject: Any = None,
    expires_delta: Union[timedelta, None] = None,
) -> str:
    sub = user_id or subject
    if not sub:
        raise ValueError("user_id or subject must be provided")

    minutes = getattr(settings, "access_token_expire_minutes", None) or getattr(
        settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 11520
    )

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)

    payload: dict[str, Any] = {"sub": str(sub), "role": role, "exp": expire}
    secret = getattr(settings, "secret_key", None) or getattr(settings, "SECRET_KEY", "secret")
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        secret = getattr(settings, "secret_key", None) or getattr(settings, "SECRET_KEY", "secret")
        return jwt.decode(token, secret, algorithms=[ALGORITHM])
    except JWTError:
        return None
