"""Authentication dependencies for protected API routes."""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.users import UserRepository
from app.schemas.auth import AuthenticatedUser
from app.security import decode_access_token


security = HTTPBearer(auto_error=False)


def authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    """Decode the bearer token and load the active user from persistence."""
    if credentials is None:
        raise authentication_error()

    try:
        payload = decode_access_token(credentials.credentials)
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject:
            raise authentication_error()
    except (jwt.InvalidTokenError, RuntimeError):
        raise authentication_error()

    user = UserRepository(db).get_by_id(subject)
    if user is None or not user.is_active:
        raise authentication_error()

    return AuthenticatedUser(id=user.id, email=user.email, name=user.name)
