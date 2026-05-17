"""Shim de compatibilidade — redireciona imports antigos para core.electrical."""
from core.electrical.circuit import Circuit, CircuitDimension

__all__ = ["Circuit", "CircuitDimension"]