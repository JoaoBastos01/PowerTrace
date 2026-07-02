"""Dataclass Opening e símbolos de portas e janelas."""
import math
from dataclasses import dataclass
from typing import Literal

from .geometry import wall_unit_vector, inward_normal


@dataclass
class Opening:
    """Descreve uma abertura (porta ou janela) em uma parede do cômodo.

    Atributos:
        wall    -- Parede onde a abertura está:
                   'S' (sul/baixo), 'N' (norte/cima),
                   'E' (leste/direita), 'W' (oeste/esquerda).
        offset  -- Distância em metros do canto inicial da parede até o início da abertura.
        width   -- Largura da abertura em metros.
        kind    -- 'door' ou 'window'.
        swing   -- Para portas: 'right' = dobradiça no lado do offset (esquerda da abertura),
                   'left' = dobradiça no lado oposto (direita da abertura).
    """
    wall:   Literal['S', 'N', 'E', 'W']
    offset: float
    width:  float
    kind:   Literal['door', 'window'] = 'door'
    swing:  Literal['right', 'left']  = 'right'


def draw_door_symbol(msp, op: Opening,
                     wall_start: tuple, wall_end: tuple) -> None:
    """Símbolo de porta conforme padrão arquitetônico.

    Desenha:
    - Linha reta da dobradiça até a ponta da folha em posição ABERTA
      (perpendicular à parede).
    - Arco de varredura da posição fechada (ao longo da parede) à
      posição aberta (inside).
    """
    (ux, uy), _ = wall_unit_vector(wall_start, wall_end)
    in_x, in_y  = inward_normal(ux, uy)
    wall_angle   = math.degrees(math.atan2(wall_end[1] - wall_start[1],
                                           wall_end[0] - wall_start[0]))
    w = op.width

    if op.swing == 'right':
        # Dobradiça no lado esquerdo da abertura (offset)
        hinge = (
            wall_start[0] + ux * op.offset,
            wall_start[1] + uy * op.offset,
        )
        open_end  = (hinge[0] + in_x * w, hinge[1] + in_y * w)
        arc_start = wall_angle % 360
        arc_end   = (wall_angle + 90) % 360
    else:  # swing == 'left'
        # Dobradiça no lado direito da abertura (offset + width)
        hinge = (
            wall_start[0] + ux * (op.offset + w),
            wall_start[1] + uy * (op.offset + w),
        )
        open_end  = (hinge[0] + in_x * w, hinge[1] + in_y * w)
        arc_start = (wall_angle + 90)  % 360
        arc_end   = (wall_angle + 180) % 360

    # Folha (posição aberta)
    msp.add_line(hinge, open_end, dxfattribs={"layer": "PT_DOORS"})

    # Arco de varredura
    msp.add_arc(
        hinge,
        radius=w,
        start_angle=arc_start,
        end_angle=arc_end,
        dxfattribs={"layer": "PT_DOORS"},
    )


def draw_window_symbol(msp, op: Opening,
                       wall_start: tuple, wall_end: tuple) -> None:
    """Símbolo de janela: duas linhas paralelas dentro da espessura da parede,
    representando o peitoril e a verga em planta.
    """
    (ux, uy), _ = wall_unit_vector(wall_start, wall_end)
    in_x, in_y  = inward_normal(ux, uy)

    inset = 0.04   # distância da face externa até a primeira linha
    depth = 0.07   # distância entre as duas linhas (< wall_thickness)

    p_start = (
        wall_start[0] + ux * op.offset,
        wall_start[1] + uy * op.offset,
    )
    p_end = (
        wall_start[0] + ux * (op.offset + op.width),
        wall_start[1] + uy * (op.offset + op.width),
    )

    for d in (inset, inset + depth):
        ox, oy = in_x * d, in_y * d
        msp.add_line(
            (p_start[0] + ox, p_start[1] + oy),
            (p_end[0]   + ox, p_end[1]   + oy),
            dxfattribs={"layer": "PT_WINDOWS"},
        )

def draw_garage_door_symbol(msp, op: Opening,
                            wall_start: tuple, wall_end: tuple) -> None:
    """Símbolo de portão de garagem (linha tracejada)."""
    (ux, uy), _ = wall_unit_vector(wall_start, wall_end)
    
    p_start = (
        wall_start[0] + ux * op.offset,
        wall_start[1] + uy * op.offset,
    )
    
    dash_len = 0.2
    gap_len = 0.15
    dist = op.width
    cursor = 0.0
    
    while cursor < dist:
        seg_end = min(cursor + dash_len, dist)
        x1 = p_start[0] + ux * cursor
        y1 = p_start[1] + uy * cursor
        x2 = p_start[0] + ux * seg_end
        y2 = p_start[1] + uy * seg_end
        msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "PT_DOORS"})
        cursor += dash_len + gap_len
