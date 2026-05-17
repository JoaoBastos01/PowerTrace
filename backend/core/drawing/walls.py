"""Desenho de paredes e estrutura de cômodos."""
from typing import List

from core.electrical.base import BaseRoom
from .openings import Opening, draw_door_symbol, draw_window_symbol


def draw_wall_segment(msp, p1: tuple, p2: tuple, gaps: list, layer: str) -> None:
    """Desenha um trecho de parede de p1 → p2 pulando os intervalos em `gaps`."""
    import math
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return

    def point_at(t):
        r = max(0.0, min(t, length)) / length
        return (p1[0] + dx * r, p1[1] + dy * r)

    sorted_gaps = sorted(gaps, key=lambda g: g[0])
    cursor = 0.0

    for gap_start, gap_end in sorted_gaps:
        if cursor < gap_start:
            msp.add_line(point_at(cursor), point_at(gap_start), dxfattribs={"layer": layer})
        cursor = max(cursor, gap_end)

    if cursor < length:
        msp.add_line(point_at(cursor), point_at(length), dxfattribs={"layer": layer})


def draw_room_structure(msp, room: BaseRoom,
                        wall_thickness: float = 0.15,
                        openings: List[Opening] = None) -> None:
    """Desenha as paredes do cômodo com suporte a aberturas (portas e janelas)."""
    if openings is None:
        openings = []

    x, y = room.origin
    w, l = room.width, room.length
    t    = wall_thickness

    ext_walls = getattr(room, 'exterior_walls', {'N', 'S', 'E', 'W'})

    ts = t if 'S' in ext_walls else t / 2.0
    tn = t if 'N' in ext_walls else t / 2.0
    te = t if 'E' in ext_walls else t / 2.0
    tw = t if 'W' in ext_walls else t / 2.0

    outer_walls = {
        'S': ((x,     y    ), (x + w, y    ), w),
        'E': ((x + w, y    ), (x + w, y + l), l),
        'N': ((x + w, y + l), (x,     y + l), w),
        'W': ((x,     y + l), (x,     y    ), l),
    }

    outer_gaps = {'S': [], 'E': [], 'N': [], 'W': []}
    inner_gaps = {'S': [], 'E': [], 'N': [], 'W': []}

    for op in openings:
        start = op.offset
        end   = op.offset + op.width
        outer_gaps[op.wall].append((start, end))
        ds = tw if op.wall == 'S' else (ts if op.wall == 'E' else (te if op.wall == 'N' else tn))
        if op.kind in ['door', 'window', 'gap']:
            inner_gaps[op.wall].append((start - ds, end - ds))

    for wid, (p1, p2, _) in outer_walls.items():
        if wid in ext_walls:
            draw_wall_segment(msp, p1, p2, outer_gaps[wid], "PT_WALLS_OUTER")

    from .geometry import wall_unit_vector, inward_normal
    inner_walls = {
        'S': ((x + tw,     y + ts    ), (x + w - te, y + ts    )),
        'E': ((x + w - te, y + ts    ), (x + w - te, y + l - tn)),
        'N': ((x + w - te, y + l - tn), (x + tw,     y + l - tn)),
        'W': ((x + tw,     y + l - tn), (x + tw,     y + ts    )),
    }
    for wid, (p1, p2) in inner_walls.items():
        draw_wall_segment(msp, p1, p2, inner_gaps[wid], "PT_WALLS_INNER")
        (ux, uy), _ = wall_unit_vector(p1, p2)
        in_x, in_y = inward_normal(ux, uy)
        seal_dist = ts if wid == 'S' else (te if wid == 'E' else (tn if wid == 'N' else tw))
        for g_start, g_end in inner_gaps[wid]:
            px1, py1 = p1[0] + ux * g_start, p1[1] + uy * g_start
            px2, py2 = p1[0] + ux * g_end,   p1[1] + uy * g_end
            msp.add_line((px1, py1), (px1 - in_x * seal_dist, py1 - in_y * seal_dist), dxfattribs={"layer": "PT_WALLS_INNER"})
            msp.add_line((px2, py2), (px2 - in_x * seal_dist, py2 - in_y * seal_dist), dxfattribs={"layer": "PT_WALLS_INNER"})

    msp.add_text(
        f"{room.name} ({room.get_total_wattage()}W)",
        dxfattribs={"height": 0.2, "layer": "PT_TEXT"}
    ).set_placement((x + w / 2, y + l / 2))

    for op in openings:
        if op.kind == 'door':
            p1, p2 = inner_walls[op.wall]
            ds = tw if op.wall == 'S' else (ts if op.wall == 'E' else (te if op.wall == 'N' else tn))
            inner_op = Opening(wall=op.wall, offset=op.offset - ds, width=op.width, kind=op.kind, swing=op.swing)
            draw_door_symbol(msp, inner_op, p1, p2)
        elif op.kind == 'window':
            p1, p2, _ = outer_walls[op.wall]
            draw_window_symbol(msp, op, p1, p2)
