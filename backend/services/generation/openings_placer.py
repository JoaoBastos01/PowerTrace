"""Shim de compatibilidade — redireciona imports antigos para core.generation."""
from core.generation.openings_placer import OpeningsPlacer

__all__ = ["OpeningsPlacer"]
