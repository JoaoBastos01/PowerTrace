"""Schemas for persisted floor-plan generation workflows."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class GenerationStatus(str, Enum):
    pending = "pending"
    generated = "generated"
    failed = "failed"


class SpecificOutletInput(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    quantity: int = Field(default=1, ge=1, le=20)
    power_w: int | None = Field(default=None, ge=1)
    voltage: Literal[127, 220] = 127
    power_factor: float = Field(default=1.0, gt=0.0, le=1.0)
    enabled: bool = True
    source: Literal["default", "custom"] = "custom"
    notes: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_contract(self):
        if self.source == "default":
            if self.quantity != 1:
                raise ValueError("Default TUE quantity must be 1.")
            if self.power_w is not None:
                raise ValueError("Default TUE power cannot be overridden.")
            return self

        if self.enabled and not self.name:
            raise ValueError("Enabled custom TUE must have a name.")

        if self.enabled and self.power_w is None:
            raise ValueError("Enabled custom TUE must have power_w defined.")

        return self


class RoomGenerationInput(BaseModel):
    room_key: str = Field(..., description="Example: kitchen or bedroom_1.")
    room_type: str = Field(..., description="Domain room type used by the generator.")
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    general_outlets_locked: bool = True
    specific_outlets: list[SpecificOutletInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_room(self):
        if self.room_key != self.room_type:
            raise ValueError("room_key must match room_type for now.")

        if not self.general_outlets_locked:
            raise ValueError("General outlets cannot be overridden.")

        outlet_ids = [outlet.id for outlet in self.specific_outlets]
        if len(outlet_ids) != len(set(outlet_ids)):
            raise ValueError("Duplicate specific outlet ids are not allowed.")

        return self


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
    def validate_rooms(
        cls,
        rooms: list[RoomGenerationInput],
    ) -> list[RoomGenerationInput]:
        room_keys = [room.room_key for room in rooms]

        if len(room_keys) != len(set(room_keys)):
            raise ValueError("Duplicate room keys are not allowed.")

        return rooms


class GeneratedSpecificOutletResult(BaseModel):
    key: str
    name: str
    power_w: int
    voltage: Literal[127, 220]
    power_factor: float
    source: Literal["default", "custom"]


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
    specific_outlets: list[GeneratedSpecificOutletResult] = Field(
        default_factory=list
    )


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
