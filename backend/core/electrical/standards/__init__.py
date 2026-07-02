"""Compatibility exports for standards, geometry and room helpers."""

from core.drawing.geometry import inward_normal, perimeter_point, wall_unit_vector

from .nbr5410 import ElectricalStandards, WireSpec
from .nbr8995 import LightingResult, lighting_calculator


def __getattr__(name: str):
    room_exports = {
        "Bathroom",
        "BathroomSocial",
        "Bedroom",
        "Corridor",
        "Garage",
        "Kitchen",
        "Living",
        "LivingKitchen",
    }
    if name in room_exports:
        from .. import rooms

        return getattr(rooms, name)
    if name == "OpeningsPlacer":
        from core.generation.openings_placer import OpeningsPlacer

        return OpeningsPlacer
    if name in {"Appliance", "ApplianceType"}:
        from .. import appliances

        return getattr(appliances, name)
    if name in {"Circuit", "CircuitDimension"}:
        from .. import circuit

        return getattr(circuit, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Bathroom",
    "BathroomSocial",
    "Appliance",
    "ApplianceType",
    "Bedroom",
    "Circuit",
    "CircuitDimension",
    "Corridor",
    "ElectricalStandards",
    "Garage",
    "Kitchen",
    "LightingResult",
    "Living",
    "LivingKitchen",
    "OpeningsPlacer",
    "WireSpec",
    "inward_normal",
    "lighting_calculator",
    "perimeter_point",
    "wall_unit_vector",
]
