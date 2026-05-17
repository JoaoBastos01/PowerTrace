"""Shim de compatibilidade — redireciona imports antigos para core.electrical.standards."""
from core.electrical.standards.nbr8995 import (
    lighting_calculator, LightingResult, REQUIRED_ILLUMINANCE,
    room_index, utilization_factor,
)

__all__ = ["lighting_calculator", "LightingResult", "REQUIRED_ILLUMINANCE", "room_index", "utilization_factor"]
