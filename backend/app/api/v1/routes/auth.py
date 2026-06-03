"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import settings

from app.dependencies.auth import get_current_user
from app.schemas.auth import (
    AuthenticatedUser,
    AuthTokenResponse,
    LoginRequest,
    UserResponse,
)
from app.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthTokenResponse)
def login(request: LoginRequest) -> AuthTokenResponse:
    """Authenticate a user and return a bearer token."""
    credentials_are_valid = (
    request.username == settings.app_username
    and request.password == settings.app_password
    )
    
    if not credentials_are_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
        
    # TODO: criar token usando o username como subject
    access_token = create_access_token(subject=request.username)

    # TODO: retornar access_token no schema AuthTokenResponse
    return AuthTokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def me(current_user: AuthenticatedUser = Depends(get_current_user)) -> UserResponse:
    """Return the authenticated user."""
    return UserResponse(id=current_user.id, username=current_user.username)

