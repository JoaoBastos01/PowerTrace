"""Shim de compatibilidade — redireciona imports antigos para core.drawing."""
from core.drawing.engine import DXFGenerator
from core.drawing.openings import Opening

__all__ = ["DXFGenerator", "Opening"]
