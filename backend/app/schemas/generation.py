"""Schemas for persisted floor-plan generation workflows."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class GenerationStatus(str, Enum):
    pending = "pending"
    generated = "generated"
    failed = "failed"


class SpecificOutletInput(BaseModel):
    id: str | None = Field(default=None, description="Stable UI id for default items.")
    name: str = Field(..., description="Example: shower, oven, air conditioner.")
    quantity: int = Field(default=1, ge=1)
    power_va: int | None = Field(default=None, ge=1)
    enabled: bool = True
    source: Literal["default", "custom"] = "custom"
    notes: str | None = None


class RoomGenerationInput(BaseModel):
    room_key: str = Field(..., description="Example: kitchen or bedroom_1.")
    room_type: str = Field(..., description="Domain room type used by the generator.")
    display_name: str | None = None
    general_outlets_locked: bool = True
    specific_outlets: list[SpecificOutletInput] = Field(default_factory=list)


class GenerationCreateRequest(BaseModel):
    width: float = Field(..., gt=0, description="House width in meters.")
    length: float = Field(..., gt=0, description="House length in meters.")
    seed: int | None = Field(
        default=None,
        ge=0,
        le=2**32 - 1,
        description="Optional deterministic 32-bit seed.",
    )
    rooms: list[RoomGenerationInput] = Field(
        default_factory=list,
        description="Reserved for a future room and TUE override release.",
    )
    output_format: Literal["dxf"] = "dxf"

    @field_validator("rooms")
    @classmethod
    def reject_room_overrides(
        cls, value: list[RoomGenerationInput]
    ) -> list[RoomGenerationInput]:
        if value:
            raise ValueError("Room and specific outlet overrides are not supported yet.")
        return value


class GeneratedRoomResult(BaseModel):
    room_type: str
    room_role: str
    name: str
    x: float
    y: float
    width: float
    length: float
    area: float
    total_wattage: int
    exterior_walls: list[str]


class GenerationResult(BaseModel):
    seed: int
    category: str
    total_width: float
    total_length: float
    total_area: float
    rooms: list[GeneratedRoomResult]
    dxf_filename: str


class GenerationCreatedResponse(BaseModel):
    project_id: str
    generation_id: str
    status: GenerationStatus
    seed: int
    message: str
    download_url: str | None = None
    error_message: str | None = None


class GenerationDetailResponse(BaseModel):
    project_id: str
    generation_id: str
    status: GenerationStatus
    seed: int
    dxf_filename: str | None = None
    error_message: str | None = None
    download_url: str | None = None
    result: GenerationResult | None = None
