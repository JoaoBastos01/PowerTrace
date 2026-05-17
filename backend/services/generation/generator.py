"""Shim de compatibilidade — redireciona imports antigos para core."""
from core.generation.generator import FloorPlanGenerator
from core.generation.openings_placer import OpeningsPlacer

__all__ = ["FloorPlanGenerator", "OpeningsPlacer"]
