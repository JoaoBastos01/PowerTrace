"""Lighting fixture symbols (ceiling lights) according to NBR 5410."""

import math

from core.electrical.appliances import ApplianceType
from core.electrical.base import BaseRoom


def _draw_lighting_symbol(msp, cx: float, cy: float, r: float = 0.05) -> None:
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


def draw_lighting(msp, room: BaseRoom) -> None:
    """Distributes lighting points along the room.

    Iterates over all ApplianceType.LIGHTING in the room and positions them
    in a uniform grid within the internal space. If no lighting fixtures
    are defined, nothing is drawn.
    """
    lights = [a for a in room.appliances if a.type == ApplianceType.LIGHTING]
    if not lights:
        return

    n = len(lights)
    # Grid: cols = ceil(sqrt(n)), rows = ceil(n / cols)
    cols = max(1, math.ceil(math.sqrt(n * room.width / room.length)))
    rows = math.ceil(n / cols)
    ex = room.width / cols      # spacing in X between luminaires
    ey = room.length / rows     # spacing in Y between luminaires
    x, y = room.origin          # origin of the room
    idx = 0
    for row in range(rows):
        for col in range(cols):
            if idx >= n:        # grid can have more cells than luminaires
                break
            cx = x + ex / 2 + col * ex
            cy = y + ey / 2 + row * ey
            _draw_lighting_symbol(msp, cx, cy)
            watt_text = f"{lights[idx].wattage}W"
            msp.add_text(watt_text, dxfattribs={"height": 0.1, "layer": "PT_TEXT"}).set_placement((cx + 0.1, cy + 0.1))
            idx += 1
