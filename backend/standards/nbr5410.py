"""Shim de compatibilidade — redireciona imports antigos para core.electrical.standards."""
from core.electrical.standards.nbr5410 import ElectricalStandards, WireSpec

__all__ = ["ElectricalStandards", "WireSpec"]