"""Schemas for the plant generation form and result workflow."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class GenerationStatus(str, Enum):
    """Lifecycle states for a generated plant."""

    pending = "pending"
    generated = "generated"
    failed = "failed"


class SpecificOutletInput(BaseModel):
    """One TUE item displayed inside a room form section.

    TUG items stay fixed for now and should be calculated by the domain layer.
    TUE defaults can be sent with source='default' and enabled=False when the
    user removes one from the form.
    """

    id: str | None = Field(default=None, description="Stable UI id for default items.")
    name: str = Field(..., description="Example: chuveiro, forno, ar-condicionado.")
    quantity: int = Field(default=1, ge=1)
    power_va: int | None = Field(default=None, ge=1)
    enabled: bool = True
    source: Literal["default", "custom"] = "custom"
    notes: str | None = None


class RoomGenerationInput(BaseModel):
    """One room section from the generation form."""

    room_key: str = Field(..., description="Example: kitchen, bedroom_1, bathroom_1.")
    room_type: str = Field(..., description="Domain room type used by the generator.")
    display_name: str | None = Field(default=None, description="Label shown in the UI.")
    general_outlets_locked: bool = Field(
        default=True,
        description="TUG values are fixed by the app at first.",
    )
    specific_outlets: list[SpecificOutletInput] = Field(default_factory=list)


class GenerationCreateRequest(BaseModel):
    """Payload submitted by the 'Gerar planta' form."""

    width: float = Field(..., gt=0, description="House width in meters.")
    length: float = Field(..., gt=0, description="House length in meters.")
    seed: int | None = Field(default=None, description="Optional deterministic seed.")
    rooms: list[RoomGenerationInput] = Field(default_factory=list)
    output_format: Literal["dxf"] = "dxf"


class GenerationCreatedResponse(BaseModel):
    """Response used by the success/failure page after generation."""

    project_id: str
    generation_id: str
    status: GenerationStatus
    http_status: int = 200
    message: str
    download_url: str | None = None


class GenerationDetailResponse(BaseModel):
    """Generation details for polling or re-opening a project."""

    project_id: str
    generation_id: str
    status: GenerationStatus
    dxf_filename: str | None = None
    error_message: str | None = None
    download_url: str | None = None

