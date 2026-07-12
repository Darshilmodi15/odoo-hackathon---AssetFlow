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
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return password_hash.verify(plain_password, hashed_password)
    except Exception:
        return False


def create_access_token(
    subject: Any,
    role: str = "employee",
    expires_delta: timedelta | None = None
) -> str:
    # If the user passed expires_delta as the second positional argument (e.g. Union[timedelta, None])
    if isinstance(role, timedelta):
        expires_delta = role
        role = "employee"

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode = {"exp": expire, "sub": str(subject), "role": role}
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


class DecodedToken(str):
    def __new__(cls, value: str, payload: dict[str, Any]):
        obj = super().__new__(cls, value)
        obj._payload = payload
        return obj

    def get(self, key: str, default: Any = None) -> Any:
        if key == "sub":
            return str(self)
        return self._payload.get(key, default)

    def __getitem__(self, key: str) -> Any:
        if key == "sub":
            return str(self)
        return self._payload[key]


def decode_access_token(token: str) -> Any | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            return None
        return DecodedToken(subject, payload)
    except JWTError:
        return None
