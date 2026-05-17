"""Shim de compatibilidade — redireciona imports antigos para core.electrical."""
from core.electrical.appliances import Appliance, ApplianceType

__all__ = ["Appliance", "ApplianceType"]
