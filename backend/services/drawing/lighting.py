"""Símbolos de pontos de iluminação (luminárias de teto) conforme NBR 5410."""
import math

from models.appliances import ApplianceType
from models.base import BaseRoom


def _draw_lighting_symbol(msp, cx: float, cy: float, r: float = 0.15) -> None:
    """Desenha um símbolo de luminária (círculo com X inscrito) em (cx, cy)."""
    d = r / math.sqrt(2)
    msp.add_circle((cx, cy), radius=r, dxfattribs={"layer": "PT_LIGHTING"})
    msp.add_line(
        (cx - d, cy - d), (cx + d, cy + d),
        dxfattribs={"layer": "PT_LIGHTING"},
    )
    msp.add_line(
        (cx + d, cy - d), (cx - d, cy + d),
        dxfattribs={"layer": "PT_LIGHTING"},
    )


def draw_lighting(msp, room: BaseRoom) -> None:
    """Distribui os pontos de iluminação ao longo do cômodo.

    Itera sobre todos os ApplianceType.LIGHTING do cômodo e os posiciona
    em grade uniforme dentro do espaço interno. Se não houver luminárias
    definidas, nada é desenhado.
    """
    lights = [a for a in room.appliances if a.type == ApplianceType.LIGHTING]
    if not lights:
        return

    n = len(lights)
    # Grade: cols = ceil(sqrt(n)), rows = ceil(n / cols)
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)

    x, y = room.origin

    for i, _ in enumerate(lights):
        col = i % cols
        row = i // cols
        # Distribui uniformemente dentro do espaço interno do cômodo
        cx = x + room.width  * (col + 1) / (cols + 1)
        cy = y + room.length * (row + 1) / (rows + 1)
        _draw_lighting_symbol(msp, cx, cy)
