"""Core floor-plan data models used by the generation pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, List, Tuple


@dataclass(frozen=True)
class RoomConfig:
    room_type: str
    min_area: float
    max_area: float
    min_dimension: float
    requires_natural_light: bool
    base_probability: float
    area_threshold: float
    weight: float


@dataclass(frozen=True)
class RoomSpec:
    room_type: str
    x: float
    y: float
    width: float
    length: float
    exterior_walls: FrozenSet[str] = field(default_factory=frozenset)

    @property
    def area(self) -> float:
        return self.width * self.length

    @property
    def origin(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass(frozen=True)
class FloorPlan:
    seed: int
    total_width: float
    total_length: float
    rooms: List[RoomSpec]

    @property
    def total_area(self) -> float:
        return self.total_width * self.total_length

