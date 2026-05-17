"""Distribuição de pontos de TUG e TUE conforme NBR 5410."""

from typing import List

from core.electrical.appliances import ApplianceType
from core.electrical.base import BaseRoom

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
    """Distribui os pontos de TUG e TUE ao longo do perímetro do cômodo."""
    if openings is None:
        openings = []

    outlets = [
        a for a in room.appliances
        if a.type in (ApplianceType.GENERAL, ApplianceType.DEDICATED)
    ]
    if not outlets:
        return

    x, y = room.origin
    width, length = room.width, room.length
    perim = 2 * (width + length)
    n = len(outlets)

    forbidden = [
        opening_to_perimeter_interval(op.wall, op.offset, op.width, width, length, margin=0.20)
        for op in openings
    ]

    free_segments = build_free_segments(perim, forbidden)
    free_length = sum(e - s for s, e in free_segments)

    spacing = free_length / n
    for i, app in enumerate(outlets):
        dist_free = spacing * i + spacing / 2
        dist_abs = map_free_to_absolute(dist_free, free_segments)
        px, py = perimeter_point(x, y, width, length, dist_abs, wall_thickness)

        msp.add_circle((px, py), radius=0.06, dxfattribs={"layer": "PT_SYMBOLS"})
        msp.add_text(
            f"{app.wattage}W", dxfattribs={"height": 0.1, "layer": "PT_TEXT"}
        ).set_placement((px + 0.07, py + 0.1))
