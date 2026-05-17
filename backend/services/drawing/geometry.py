"""Shim de compatibilidade — redireciona imports antigos para core.drawing."""
from core.drawing.geometry import (
    perimeter_point, wall_unit_vector, inward_normal,
    opening_to_perimeter_interval, build_free_segments, map_free_to_absolute,
)

__all__ = [
    "perimeter_point", "wall_unit_vector", "inward_normal",
    "opening_to_perimeter_interval", "build_free_segments", "map_free_to_absolute",
]
