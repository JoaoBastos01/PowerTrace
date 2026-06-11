"""Registration and authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import authentication_error, get_current_user
from app.repositories.users import UserRepository
from app.schemas.auth import (
    AuthenticatedUser,
    AuthTokenResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from app.security import create_access_token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Create a public user account."""
    repo = UserRepository(db)
    if repo.get_by_email(str(request.email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    try:
        user = repo.create(request)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    return UserResponse.model_validate(user)


@router.post("/login", response_model=AuthTokenResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
) -> AuthTokenResponse:
    """Authenticate an active user and return a bearer token."""
    user = UserRepository(db).authenticate(str(request.email), request.password)
    if user is None:
        raise authentication_error()
    return AuthTokenResponse(access_token=create_access_token(subject=user.id))


@router.get("/me", response_model=UserResponse)
def me(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UserResponse:
    """Return the authenticated user's public profile."""
    return UserResponse.model_validate(current_user)
