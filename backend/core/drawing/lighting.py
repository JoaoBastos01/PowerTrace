"""Lighting fixture symbols (ceiling lights) according to NBR 5410."""

import math

from core.electrical.appliances import ApplianceType
from core.electrical.base import BaseRoom


def draw_lighting_symbol(msp, cx: float, cy: float, r: float = 0.05) -> None:
    """Draws a lighting symbol (circle with inscribed X) at (cx, cy)."""
    d = r / math.sqrt(2)
    msp.add_circle((cx, cy), radius=r, dxfattribs={"layer": "PT_LIGHTING"})
    msp.add_line(
        (cx - d, cy - d),
        (cx + d, cy + d),
        dxfattribs={"layer": "PT_LIGHTING"},
    )
    msp.add_line(
        (cx + d, cy - d),
        (cx - d, cy + d),
        dxfattribs={"layer": "PT_LIGHTING"},
    )


def _lighting_grid_dimensions(
    count: int,
    width: float,
    length: float,
    linear_aspect_threshold: float = 3.0,
) -> tuple[int, int]:
    """Return columns and rows for a balanced residential lighting grid."""
    short_side = min(width, length)
    long_side = max(width, length)
    if count > 1 and short_side > 0:
        aspect_ratio = long_side / short_side
        if aspect_ratio >= linear_aspect_threshold:
            if width >= length:
                return count, 1
            return 1, count

    cols = max(1, math.ceil(math.sqrt(count)))
    rows = math.ceil(count / cols)

    # Keep two-light layouts aligned with the room's dominant direction.
    if count == 2 and length > width:
        return rows, cols
    return cols, rows


def _lighting_positions(
    origin: tuple,
    width: float,
    length: float,
    count: int,
    wall_thickness: float = 0.15,
) -> list[tuple[float, float]]:
    t = wall_thickness
    x0 = origin[0] + t
    y0 = origin[1] + t
    int_w = width - 2 * t
    int_l = length - 2 * t

    if count <= 0 or int_w <= 0 or int_l <= 0:
        return []

    cols, rows = _lighting_grid_dimensions(count, int_w, int_l)
    ex = int_w / cols
    ey = int_l / rows
    positions = []
    for row in range(rows):
        for col in range(cols):
            if len(positions) >= count:
                return positions
            cx = x0 + ex / 2 + col * ex
            cy = y0 + ey / 2 + row * ey
            positions.append((cx, cy))
    return positions


def draw_lighting(msp, room: BaseRoom, wall_thickness: float = 0.15) -> None:
    """Distributes lighting points along the room.

    Iterates over all ApplianceType.LIGHTING in the room and positions them
    in a uniform grid within the internal space. If no lighting fixtures
    are defined, nothing is drawn.
    """
    lights = [a for a in room.appliances if a.type == ApplianceType.LIGHTING]
    if not lights:
        return

    positions = _lighting_positions(
        room.origin,
        room.width,
        room.length,
        len(lights),
        wall_thickness,
    )
    for idx, (cx, cy) in enumerate(positions):
        draw_lighting_symbol(msp, cx, cy)
        watt_text = f"{lights[idx].wattage}W"
        msp.add_text(watt_text, dxfattribs={"height": 0.1, "layer": "PT_TEXT"}).set_placement((cx + 0.1, cy + 0.1))
