"""Distribuição de pontos de TUG (Tomadas de Uso Geral) e TUE (Tomadas de Uso Específico) conforme NBR 5410."""

from typing import List

from models.appliances import ApplianceType
from models.base import BaseRoom

from .geometry import (
    perimeter_point,
    opening_to_perimeter_interval,
    build_free_segments,
    map_free_to_absolute,
)


def draw_appliances(
    msp,
    room: BaseRoom,
    wall_thickness: float = 0.15,
    openings: List = None,
) -> None:
    """Distribui os pontos de TUG e TUE ao longo do perímetro do cômodo.

    Conforme NBR 5410, as tomadas de uso geral (TUG) devem ser espaçadas
    por no máximo 3,5 m de perímetro. As tomadas de uso específico (TUE)
    também são posicionadas no perímetro. Apenas ApplianceType.GENERAL e
    ApplianceType.DEDICATED são tratadas aqui — luminárias (LIGHTING) são
    tratadas pela draw_lighting e não entram aqui.

    Quando `openings` é fornecido, nenhuma tomada é posicionada sobre ou
    imediatamente adjacente a portas ou janelas (margem padrão de 0,20 m).
    O percurso segue a ordem: Sul → Leste → Norte → Oeste.
    """
    if openings is None:
        openings = []

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
    n = len(outlets)

    # ── Zonas proibidas a partir das aberturas ────────────────────────────
    forbidden = [
        opening_to_perimeter_interval(
            op.wall, op.offset, op.width, width, length, margin=0.20
        )
        for op in openings
    ]

    free_segments = build_free_segments(perim, forbidden)
    free_length = sum(e - s for s, e in free_segments)

    # ── Distribuição uniforme no espaço livre ─────────────────────────────
    spacing = free_length / n
    for i, app in enumerate(outlets):
        dist_free = spacing * i + spacing / 2
        dist_abs = map_free_to_absolute(dist_free, free_segments)
        px, py = perimeter_point(x, y, width, length, dist_abs, wall_thickness)

        # Símbolo: círculo (TUG / TUE)
        msp.add_circle((px, py), radius=0.06, dxfattribs={"layer": "PT_SYMBOLS"})
        # Etiqueta de potência
        msp.add_text(
            f"{app.wattage}W", dxfattribs={"height": 0.1, "layer": "PT_TEXT"}
        ).set_placement((px + 0.07, py + 0.1))
