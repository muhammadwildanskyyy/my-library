"""
JWT authentication utilities — token creation and verification.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config.settings import Settings, get_settings

# ---------------------------------------------------------------------------
# Security scheme
# ---------------------------------------------------------------------------
_bearer_scheme = HTTPBearer()


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
def hash_password(plain: str) -> str:
    """Hash a plain-text password with bcrypt."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Check a plain-text password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# JWT token helpers
# ---------------------------------------------------------------------------
def create_access_token(
    user_id: UUID,
    settings: Settings | None = None,
) -> str:
    """Create a signed JWT access token."""
    s = settings or get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=s.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, s.JWT_SECRET_KEY, algorithm=s.JWT_ALGORITHM)


def decode_access_token(token: str, settings: Settings | None = None) -> dict:
    """Decode and validate a JWT access token. Raises on failure."""
    s = settings or get_settings()
    try:
        return jwt.decode(token, s.JWT_SECRET_KEY, algorithms=[s.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
        )


# ---------------------------------------------------------------------------
# FastAPI dependency — extract current user_id from Bearer token
# ---------------------------------------------------------------------------
def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> str:
    """Extract and return the `user_id` (as string UUID) from the JWT."""
    payload = decode_access_token(credentials.credentials, settings)
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim.",
        )
    return user_id
