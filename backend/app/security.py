"""Authentication token helpers."""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.config import settings


ALGORITHM = "HS256"


def create_access_token(subject: str) -> str:
    """Create a JWT access token."""
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
 