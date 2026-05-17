"""Shim de compatibilidade — redireciona imports antigos para core.generation."""
from core.generation.generator import FloorPlanGenerator
from core.generation.openings_placer import OpeningsPlacer

__all__ = ["FloorPlanGenerator", "OpeningsPlacer"]
