"""Pydantic schemas for simple authentication."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Credentials submitted by the login form."""

    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class AuthTokenResponse(BaseModel):
    """Token returned after a successful login."""

    access_token: str
    token_type: str = "bearer"


class AuthenticatedUser(BaseModel):
    """Minimal authenticated user exposed to route handlers."""

    id: str
    username: str


class UserResponse(BaseModel):
    """Public user payload."""

    id: str
    username: str

