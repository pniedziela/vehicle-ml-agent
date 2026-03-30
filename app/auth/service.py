"""JWT-based authentication for the single recruiter account."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_bearer = HTTPBearer()


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def authenticate(username: str, password: str) -> bool:
    """Return True if credentials match the configured single account."""
    if username != settings.AUTH_USERNAME:
        return False
    # Compare directly (plain password in env) – acceptable for a demo account.
    # For production you'd store a bcrypt hash instead.
    return password == settings.AUTH_PASSWORD


def create_access_token() -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": settings.AUTH_USERNAME, "exp": expire},
        settings.SECRET_KEY,
        algorithm="HS256",
    )


def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    """FastAPI dependency – raises 401 if token is missing or invalid."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nieprawidłowy lub wygasły token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=["HS256"],
        )
        sub: str | None = payload.get("sub")
        if sub != settings.AUTH_USERNAME:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return sub
