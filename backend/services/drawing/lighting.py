"""Símbolo de ponto de iluminação (luminária de teto)."""
import math

from models.base import BaseRoom


def draw_lighting(msp, room: BaseRoom) -> None:
    """Símbolo de ponto de iluminação no centro do cômodo.

    Convenção de planta baixa elétrica: círculo com X inscrito,
    representando a luminária de teto (ponto de luz).
    """
    x, y = room.origin
    cx = x + room.width  / 2
    cy = y + room.length / 2
    r  = 0.15            # raio do símbolo (metros)
    d  = r / math.sqrt(2)

    msp.add_circle(
        (cx, cy), radius=r, dxfattribs={"layer": "PT_LIGHTING"}
    )
    # Diagonais formando o X
    msp.add_line(
        (cx - d, cy - d), (cx + d, cy + d),
        dxfattribs={"layer": "PT_LIGHTING"}
    )
    msp.add_line(
        (cx + d, cy - d), (cx - d, cy + d),
        dxfattribs={"layer": "PT_LIGHTING"}
    )
