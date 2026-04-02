"""Distribuição de pontos de TUG (Tomadas de Uso Geral) conforme NBR 5410."""
from models.base import BaseRoom

from .geometry import perimeter_point


def draw_appliances(msp, room: BaseRoom,
                    wall_thickness: float = 0.15) -> None:
    """Distribui os pontos de TUG ao longo do perímetro do cômodo.

    Conforme NBR 5410, as tomadas de uso geral devem ser espaçadas por
    no máximo 3,5 m de perímetro. Esta função distribui os pontos
    uniformemente ao redor das 4 paredes, na face interna da alvenaria.

    O percurso segue a ordem: Sul → Leste → Norte → Oeste.
    """
    if not room.appliances:
        return

    x, y = room.origin
    w, l = room.width, room.length
    n       = len(room.appliances)
    perim   = 2 * (w + l)
    spacing = perim / n

    for i, app in enumerate(room.appliances):
        # Posição no centro de cada intervalo de spacing
        dist = spacing * i + spacing / 2
        px, py = perimeter_point(x, y, w, l, dist, wall_thickness)

        # Símbolo: círculo (TUG)
        msp.add_circle(
            (px, py), radius=0.06, dxfattribs={"layer": "PT_SYMBOLS"}
        )
        # Etiqueta de potência
        msp.add_text(
            f"{app.wattage}W",
            dxfattribs={"height": 0.1, "layer": "PT_TEXT"}
        ).set_placement((px + 0.07, py + 0.1))
