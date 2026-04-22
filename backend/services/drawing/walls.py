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

    ext_walls = getattr(room, 'exterior_walls', {'N', 'S', 'E', 'W'})

    # Fatores de encolhimento para tratar paredes compartilhadas = t/2. Rua = t.
    ts = t if 'S' in ext_walls else t / 2.0
    tn = t if 'N' in ext_walls else t / 2.0
    te = t if 'E' in ext_walls else t / 2.0
    tw = t if 'W' in ext_walls else t / 2.0

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
        
        # Diferente offset shift dependo da parede:
        ds = tw if op.wall == 'S' else (ts if op.wall == 'E' else (te if op.wall == 'N' else tn))
        
        if op.kind in ['door', 'window', 'gap']:
            # Puncionando o inner_wall em aberturas E no cômodo passivo 'gap'
            inner_gaps[op.wall].append((start - ds, end - ds))

    # ---- Paredes externas ----
    for wid, (p1, p2, _) in outer_walls.items():
        if wid in ext_walls:  # SÓ desenha muro se ele for exterior!
            draw_wall_segment(msp, p1, p2, outer_gaps[wid], "PT_WALLS_OUTER")

    # ---- Paredes internas (Puncionamentos e Esquadrias Masonry) ----
    from .geometry import wall_unit_vector, inward_normal
    inner_walls = {
        'S': ((x + tw,     y + ts    ), (x + w - te, y + ts    )),
        'E': ((x + w - te, y + ts    ), (x + w - te, y + l - tn)),
        'N': ((x + w - te, y + l - tn), (x + tw,     y + l - tn)),
        'W': ((x + tw,     y + l - tn), (x + tw,     y + ts    )),
    }
    for wid, (p1, p2) in inner_walls.items():
        draw_wall_segment(msp, p1, p2, inner_gaps[wid], "PT_WALLS_INNER")
        
        # Selar as cabeceiras cortadas com as tampas perpendiculares (Fechamento da Alvenaria DXF)
        (ux, uy), _ = wall_unit_vector(p1, p2)
        in_x, in_y = inward_normal(ux, uy)
        seal_dist = ts if wid == 'S' else (te if wid == 'E' else (tn if wid == 'N' else tw))
        
        for g_start, g_end in inner_gaps[wid]:
            px1, py1 = p1[0] + ux * g_start, p1[1] + uy * g_start
            px2, py2 = p1[0] + ux * g_end,   p1[1] + uy * g_end
            
            # Linha desenha do recuo de dentro da sala para 'fora' (-in_x) selando no osso geométrico do vizinho
            msp.add_line((px1, py1), (px1 - in_x * seal_dist, py1 - in_y * seal_dist), dxfattribs={"layer": "PT_WALLS_INNER"})
            msp.add_line((px2, py2), (px2 - in_x * seal_dist, py2 - in_y * seal_dist), dxfattribs={"layer": "PT_WALLS_INNER"})

    # ---- Legenda central ----
    msp.add_text(
        f"{room.name} ({room.get_total_wattage()}W)",
        dxfattribs={"height": 0.2, "layer": "PT_TEXT"}
    ).set_placement((x + w / 2, y + l / 2))

    # ---- Símbolos das aberturas ----
    for op in openings:
        if op.kind == 'door':
            # Portas penduram-se na face INTERNA (linha ciano) para o swing não flutuar
            p1, p2 = inner_walls[op.wall]
            ds = tw if op.wall == 'S' else (ts if op.wall == 'E' else (te if op.wall == 'N' else tn))
            
            # Reposiciona o offset do simbolo da porta para a reta interna encolhida
            inner_op = Opening(wall=op.wall, offset=op.offset - ds, width=op.width, kind=op.kind, swing=op.swing)
            draw_door_symbol(msp, inner_op, p1, p2)
            
        elif op.kind == 'window':
            # Janelas penduram-se na face EXTERNA
            p1, p2, _ = outer_walls[op.wall]
            draw_window_symbol(msp, op, p1, p2)
            
        # Importante: Se op.kind == 'gap', não renderiza símbolos matemáticos (usado para o quarto não desenhar a porta de novo, cedendo pra sala)
