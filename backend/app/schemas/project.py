"""Pydantic schemas for project persistence."""

from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    """Payload for creating a saved project."""

    name: str = Field(..., min_length=1, max_length=120)
    description: str | None = None


class ProjectResponse(BaseModel):
    """Saved project summary."""

    id: str
    name: str
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProjectListResponse(BaseModel):
    """List wrapper for project index pages."""

    items: list[ProjectResponse]

