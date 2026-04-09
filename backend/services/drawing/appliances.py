"""Distribuição de pontos de TUG (Tomadas de Uso Geral) e TUE (Tomadas de Uso Específico) conforme NBR 5410."""

from models.appliances import ApplianceType
from models.base import BaseRoom

from .geometry import perimeter_point


def draw_appliances(msp, room: BaseRoom, wall_thickness: float = 0.15) -> None:
    """Distribui os pontos de TUG e TUE ao longo do perímetro do cômodo.
    Conforme NBR 5410, as tomadas de uso geral (TUG) devem ser espaçadas
    por no máximo 3,5 m de perímetro. As tomadas de uso específico (TUE)
    também são posicionadas no perímetro. Apenas ApplianceType.GENERAL e
    ApplianceType.DEDICATED são tratadas aqui — luminárias (LIGHTING) são
    tratadas pela draw_lighting e não entram aqui.
    O percurso segue a ordem: Sul → Leste → Norte → Oeste.
    """
    outlets = [
        a
        for a in room.appliances
        if a.type in (ApplianceType.GENERAL, ApplianceType.DEDICATED)
    ]
    if not outlets:
        return
    x, y = room.origin
    width, length = room.width, room.length
    perim = 2 * (width + length)
    n = len(outlets)  # ← tamanho da lista filtrada
    spacing = perim / n
    for i, app in enumerate(outlets):  # ← itera sobre outlets
        dist = spacing * i + spacing / 2
        px, py = perimeter_point(x, y, width, length, dist, wall_thickness)
        # Símbolo: círculo (TUG / TUE)
        msp.add_circle((px, py), radius=0.06, dxfattribs={"layer": "PT_SYMBOLS"})
        # Etiqueta de potência
        msp.add_text(
            f"{app.wattage}W", dxfattribs={"height": 0.1, "layer": "PT_TEXT"}
        ).set_placement((px + 0.07, py + 0.1))
