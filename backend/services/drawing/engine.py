import ezdxf
import math
from dataclasses import dataclass, field
from typing import List, Literal
from backend.models.base import BaseRoom


@dataclass
class Opening:
    """Descreve uma abertura (porta ou janela) em uma parede do cômodo.

    Atributos:
        wall    -- Parede onde a abertura está: 'S' (sul/baixo), 'N' (norte/cima),
                   'E' (leste/direita), 'W' (oeste/esquerda).
        offset  -- Distância em metros do canto inicial da parede até o início da abertura.
        width   -- Largura da abertura em metros.
        kind    -- 'door' ou 'window'.
        swing   -- Para portas: direção da folha ('right' ou 'left').
    """
    wall:   Literal['S', 'N', 'E', 'W']
    offset: float
    width:  float
    kind:   Literal['door', 'window'] = 'door'
    swing:  Literal['right', 'left']  = 'right'


class DXFGenerator:
    def __init__(self):
        self.doc = ezdxf.new(setup=True)
        self.msp = self.doc.modelspace()
        self._setup_layers()

    # ------------------------------------------------------------------
    # Layers
    # ------------------------------------------------------------------

    def _setup_layers(self):
        self.doc.layers.add(name="PT_WALLS_OUTER", color=7)  # White/Black
        self.doc.layers.add(name="PT_WALLS_INNER", color=8)  # Grey
        self.doc.layers.add(name="PT_DOORS",       color=1)  # Red
        self.doc.layers.add(name="PT_WINDOWS",     color=4)  # Cyan
        self.doc.layers.add(name="PT_LIGHTING",    color=2)  # Yellow
        self.doc.layers.add(name="PT_TEXT",        color=7)  # White
        self.doc.layers.add(name="PT_SYMBOLS",     color=3)  # Green

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _draw_wall_segment(self, p1, p2, gaps: list, layer: str):
        """Desenha um segmento de parede de p1 → p2 com lacunas (gaps).

        Cada gap é uma tupla (start_t, end_t) em metros ao longo do segmento,
        medida desde p1. O segmento é dividido em partes que evitam esses intervalos.
        """
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.hypot(dx, dy)

        if length == 0:
            return

        # Normaliza os gaps e ordena pelo início
        sorted_gaps = sorted(gaps, key=lambda g: g[0])

        cursor = 0.0  # posição atual em metros ao longo do segmento

        def point_at(t):
            ratio = t / length
            return (p1[0] + dx * ratio, p1[1] + dy * ratio)

        for gap_start, gap_end in sorted_gaps:
            if cursor < gap_start:
                self.msp.add_line(point_at(cursor), point_at(gap_start),
                                  dxfattribs={"layer": layer})
            cursor = max(cursor, gap_end)

        # Trecho final após o último gap
        if cursor < length:
            self.msp.add_line(point_at(cursor), point_at(length),
                              dxfattribs={"layer": layer})

    def _opening_gap(self, opening: Opening, wall_length: float):
        """Retorna a tupla (start_t, end_t) em metros para uma abertura numa parede."""
        start = opening.offset
        end   = opening.offset + opening.width
        return (start, end)

    # ------------------------------------------------------------------
    # Public drawing methods
    # ------------------------------------------------------------------

    def draw_room_structure(self, room: BaseRoom,
                            wall_thickness: float = 0.15,
                            openings: List[Opening] = None):
        """Desenha as paredes do cômodo com suporte a aberturas (portas/janelas).

        - Paredes são desenhadas como segmentos individuais para permitir 'punching'.
        - Openings definem lacunas nas paredes externas onde portas/janelas serão inseridas.
        - A parede interna (linha de contorno interno) é desenhada sem lacunas para
          representar a espessura estrutural da alvenaria.

        Parâmetros:
            room            -- O objeto BaseRoom com origin, width e length.
            wall_thickness  -- Espessura da parede em metros (padrão: 0.15m = 15cm).
            openings        -- Lista de Opening descrevendo portasq e janelas.
        """
        if openings is None:
            openings = []

        x, y = room.origin
        w, l = room.width, room.length
        t = wall_thickness

        # As 4 paredes externas, em ordem: sul, leste, norte, oeste
        # Definem: ponto inicial, ponto final, comprimento, identificador de parede
        walls = {
            'S': ((x,     y    ), (x + w, y    ), w),
            'E': ((x + w, y    ), (x + w, y + l), l),
            'N': ((x + w, y + l), (x,     y + l), w),
            'W': ((x,     y + l), (x,     y    ), l),
        }

        # Agrupa gaps por parede
        gaps_by_wall = {'S': [], 'E': [], 'N': [], 'W': []}
        for op in openings:
            wall_len = walls[op.wall][2]
            gaps_by_wall[op.wall].append(self._opening_gap(op, wall_len))

        # Desenha as paredes externas com as lacunas
        for wall_id, (p1, p2, _) in walls.items():
            self._draw_wall_segment(p1, p2, gaps_by_wall[wall_id], "PT_WALLS_OUTER")

        # Parede interna (sem lacunas — representa a estrutura da alvenaria)
        inner = [
            (x + t,     y + t    ),
            (x + w - t, y + t    ),
            (x + w - t, y + l - t),
            (x + t,     y + l - t),
            (x + t,     y + t    ),
        ]
        self.msp.add_lwpolyline(inner, dxfattribs={'layer': 'PT_WALLS_INNER'})

        # Legenda central do cômodo
        label_pos = (x + w / 2, y + l / 2 + 0.4)
        self.msp.add_text(
            f"{room.name} ({room.get_total_wattage()}W)",
            dxfattribs={"height": 0.2, "layer": "PT_TEXT"}
        ).set_placement(label_pos)

        # Desenha os símbolos das aberturas
        for op in openings:
            self._draw_opening_symbol(op, walls[op.wall])

    def _draw_opening_symbol(self, op: Opening, wall_def: tuple):
        """Despacha para o símbolo correto de acordo com o tipo de abertura."""
        p1, p2, wall_len = wall_def
        if op.kind == 'door':
            self._draw_door_symbol(op, p1, p2)
        else:
            self._draw_window_symbol(op, p1, p2)

    def _draw_door_symbol(self, op: Opening, wall_start: tuple, wall_end: tuple):
        """Desenha o símbolo de porta: folha reta + arco de varredura.

        A folha e o arco são posicionados e rotacionados automaticamente
        de acordo com a parede (S/N/E/W) e o sentido de abertura (right/left).
        """
        dx = wall_end[0] - wall_start[0]
        dy = wall_end[1] - wall_start[1]
        wall_length = math.hypot(dx, dy)

        # Vetor unitário ao longo da parede
        ux = dx / wall_length
        uy = dy / wall_length

        # Ângulo da parede em graus (para o arco)
        wall_angle = math.degrees(math.atan2(dy, dx))

        # Ponto de dobradiça (hinge): canto do lado de abertura
        if op.swing == 'right':
            hinge_t = op.offset
        else:
            hinge_t = op.offset + op.width

        hinge = (
            wall_start[0] + ux * hinge_t,
            wall_start[1] + uy * hinge_t,
        )

        # Sentido da folha: +90° (para dentro do cômodo, por convenção)
        if op.swing == 'right':
            leaf_angle_start = wall_angle
            leaf_angle_end   = wall_angle + 90
        else:
            leaf_angle_start = wall_angle + 180 - 90
            leaf_angle_end   = wall_angle + 180

        w = op.width

        # Ponta da folha (linha reta da dobradiça)
        leaf_end = (
            hinge[0] + math.cos(math.radians(leaf_angle_start)) * w,
            hinge[1] + math.sin(math.radians(leaf_angle_start)) * w,
        )

        # Linha da folha da porta
        self.msp.add_line(hinge, leaf_end, dxfattribs={"layer": "PT_DOORS"})

        # Arco de varredura
        self.msp.add_arc(
            hinge,
            radius=w,
            start_angle=min(leaf_angle_start, leaf_angle_end),
            end_angle=max(leaf_angle_start, leaf_angle_end),
            dxfattribs={"layer": "PT_DOORS"},
        )

    def _draw_window_symbol(self, op: Opening, wall_start: tuple, wall_end: tuple):
        """Desenha o símbolo de janela: duas linhas paralelas dentro da espessura da parede."""
        dx = wall_end[0] - wall_start[0]
        dy = wall_end[1] - wall_start[1]
        wall_length = math.hypot(dx, dy)

        ux = dx / wall_length
        uy = dy / wall_length

        # Normal interna (90° anti-horário do vetor da parede)
        nx = -uy
        ny =  ux

        gap = 0.05   # recuo da linha em relação à face da parede
        depth = 0.10 # profundidade entre as duas linhas (< wall_thickness)

        p_start = (wall_start[0] + ux * op.offset,
                   wall_start[1] + uy * op.offset)
        p_end   = (wall_start[0] + ux * (op.offset + op.width),
                   wall_start[1] + uy * (op.offset + op.width))

        for d in (gap, gap + depth):
            offset_x = nx * d
            offset_y = ny * d
            self.msp.add_line(
                (p_start[0] + offset_x, p_start[1] + offset_y),
                (p_end[0]   + offset_x, p_end[1]   + offset_y),
                dxfattribs={"layer": "PT_WINDOWS"},
            )

    # ------------------------------------------------------------------
    # Lighting & Appliances
    # ------------------------------------------------------------------

    def draw_lighting(self, room: BaseRoom):
        """Placeholder — será implementado com blocos da biblioteca de símbolos."""
        pass

    def draw_appliances(self, room: BaseRoom):
        x, y = room.origin
        if not room.appliances:
            return

        spacing = room.width / (len(room.appliances) + 1)

        for i, app in enumerate(room.appliances):
            pos_x = x + (spacing * (i + 1))
            pos_y = y + 0.2

            self.msp.add_circle(
                (pos_x, pos_y), radius=0.05, dxfattribs={"layer": "PT_SYMBOLS"}
            )
            self.msp.add_text(
                f"{app.wattage}W", dxfattribs={"height": 0.1, "layer": "PT_TEXT"}
            ).set_placement((pos_x, pos_y + 0.1))

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save(self, filename="output.dxf"):
        self.doc.saveas(filename)
        print(f"Arquivo DXF salvo como '{filename}'")
