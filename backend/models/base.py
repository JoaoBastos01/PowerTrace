"""Shim de compatibilidade — redireciona imports antigos para core.electrical."""
from core.electrical.base import BaseRoom

__all__ = ["BaseRoom"]
