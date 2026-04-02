"""Desenho de paredes e estrutura de cômodos."""
from typing import List

from models.base import BaseRoom

from .openings import Opening, draw_door_symbol, draw_window_symbol


def draw_wall_segment(msp, p1: tuple, p2: tuple,
                      gaps: list, layer: str) -> None:
    """Desenha um trecho de parede de p1 → p2 pulando os intervalos em `gaps`.

    Cada gap é (start_t, end_t) em metros ao longo do segmento desde p1.
    """
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
            msp.add_line(point_at(cursor), point_at(gap_start),
                         dxfattribs={"layer": layer})
        cursor = max(cursor, gap_end)

    if cursor < length:
        msp.add_line(point_at(cursor), point_at(length),
                     dxfattribs={"layer": layer})


def draw_room_structure(msp, room: BaseRoom,
                        wall_thickness: float = 0.15,
                        openings: List[Opening] = None) -> None:
    """Desenha as paredes do cômodo com suporte a aberturas (portas e janelas).

    Tanto a face externa quanto a face interna das paredes são 'puncionadas'
    nos pontos de porta (a janela mantém o peitoril na face interna).

    Parâmetros:
        msp            -- Model space ezdxf.
        room           -- Objeto BaseRoom com origin, width e length.
        wall_thickness -- Espessura da alvenaria em metros (padrão 15 cm).
        openings       -- Lista de Opening descrevendo portas e janelas.
    """
    if openings is None:
        openings = []

    x, y = room.origin
    w, l = room.width, room.length
    t    = wall_thickness

    # ---- Definição das 4 paredes externas (p1, p2, comprimento) ----
    outer_walls = {
        'S': ((x,     y    ), (x + w, y    ), w),
        'E': ((x + w, y    ), (x + w, y + l), l),
        'N': ((x + w, y + l), (x,     y + l), w),
        'W': ((x,     y + l), (x,     y    ), l),
    }

    # ---- Gaps por parede ----
    outer_gaps = {'S': [], 'E': [], 'N': [], 'W': []}
    inner_gaps = {'S': [], 'E': [], 'N': [], 'W': []}

    for op in openings:
        start = op.offset
        end   = op.offset + op.width
        outer_gaps[op.wall].append((start, end))
        if op.kind == 'door':
            # A face interna tem o mesmo gap com offset de -t (espessura)
            inner_gaps[op.wall].append((start - t, end - t))

    # ---- Paredes externas ----
    for wid, (p1, p2, _) in outer_walls.items():
        draw_wall_segment(msp, p1, p2, outer_gaps[wid], "PT_WALLS_OUTER")

    # ---- Paredes internas ----
    inner_walls = {
        'S': ((x + t,     y + t    ), (x + w - t, y + t    )),
        'E': ((x + w - t, y + t    ), (x + w - t, y + l - t)),
        'N': ((x + w - t, y + l - t), (x + t,     y + l - t)),
        'W': ((x + t,     y + l - t), (x + t,     y + t    )),
    }
    for wid, (p1, p2) in inner_walls.items():
        draw_wall_segment(msp, p1, p2, inner_gaps[wid], "PT_WALLS_INNER")

    # ---- Legenda central ----
    msp.add_text(
        f"{room.name} ({room.get_total_wattage()}W)",
        dxfattribs={"height": 0.2, "layer": "PT_TEXT"}
    ).set_placement((x + w / 2, y + l / 2))

    # ---- Símbolos das aberturas ----
    for op in openings:
        p1, p2, _ = outer_walls[op.wall]
        if op.kind == 'door':
            draw_door_symbol(msp, op, p1, p2)
        else:
            draw_window_symbol(msp, op, p1, p2)
