import ezdxf
import math
from dataclasses import dataclass
from typing import List, Literal
from backend.models.base import BaseRoom


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

    def _draw_wall_segment(self, p1: tuple, p2: tuple, gaps: list, layer: str):
        """Desenha um trecho de parede de p1 → p2 pulando os intervalos em `gaps`.

        Cada gap é (start_t, end_t) em metros ao longo do segmento desde p1.
        """
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
                self.msp.add_line(point_at(cursor), point_at(gap_start),
                                  dxfattribs={"layer": layer})
            cursor = max(cursor, gap_end)

        if cursor < length:
            self.msp.add_line(point_at(cursor), point_at(length),
                              dxfattribs={"layer": layer})

    def _perimeter_point(self, x: float, y: float, w: float, l: float,
                         dist: float, t: float = 0.15) -> tuple:
        """Converte uma distância ao longo do perímetro em coordenada (px, py).

        O caminho percorre as paredes em ordem: S → E → N → W.
        O ponto resultante é deslocado `t` metros para dentro do cômodo, ficando
        encostado na face interna da parede — posição padrão de TUGs conforme NBR 5410.

        Parâmetros:
            x, y  -- Origem (canto SW) do cômodo.
            w, l  -- Largura e comprimento.
            dist  -- Distância ao longo do perímetro, em metros.
            t     -- Deslocamento inward (espessura da parede).
        """
        perim = 2 * (w + l)
        dist  = dist % perim

        if dist <= w:                            # Parede S: esquerda → direita
            return (x + dist, y + t)
        dist -= w
        if dist <= l:                            # Parede E: baixo → cima
            return (x + w - t, y + dist)
        dist -= l
        if dist <= w:                            # Parede N: direita → esquerda
            return (x + w - dist, y + l - t)
        dist -= w
        return (x + t, y + l - dist)            # Parede W: cima → baixo

    # ------------------------------------------------------------------
    # Room structure
    # ------------------------------------------------------------------

    def draw_room_structure(self, room: BaseRoom,
                            wall_thickness: float = 0.15,
                            openings: List[Opening] = None):
        """Desenha as paredes do cômodo com suporte a aberturas (portas e janelas).

        Tanto a face externa quanto a face interna das paredes são 'puncionadas'
        nos pontos de porta (a janela mantém o peitoril na face interna).

        Parâmetros:
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
                # A face interna tem o mesmo gap (mesmas coordenadas absolutas),
                # mas o início do segmento interno está deslocado t metros
                inner_gaps[op.wall].append((start - t, end - t))

        # ---- Paredes externas ----
        for wid, (p1, p2, _) in outer_walls.items():
            self._draw_wall_segment(p1, p2, outer_gaps[wid], "PT_WALLS_OUTER")

        # ---- Paredes internas (4 segmentos separados para suportar punchthrough) ----
        inner_walls = {
            'S': ((x + t,     y + t    ), (x + w - t, y + t    )),
            'E': ((x + w - t, y + t    ), (x + w - t, y + l - t)),
            'N': ((x + w - t, y + l - t), (x + t,     y + l - t)),
            'W': ((x + t,     y + l - t), (x + t,     y + t    )),
        }
        for wid, (p1, p2) in inner_walls.items():
            self._draw_wall_segment(p1, p2, inner_gaps[wid], "PT_WALLS_INNER")

        # ---- Legenda central ----
        self.msp.add_text(
            f"{room.name} ({room.get_total_wattage()}W)",
            dxfattribs={"height": 0.2, "layer": "PT_TEXT"}
        ).set_placement((x + w / 2, y + l / 2))

        # ---- Símbolos das aberturas ----
        for op in openings:
            p1, p2, _ = outer_walls[op.wall]
            if op.kind == 'door':
                self._draw_door_symbol(op, p1, p2)
            else:
                self._draw_window_symbol(op, p1, p2)

    # ------------------------------------------------------------------
    # Opening symbols
    # ------------------------------------------------------------------

    def _draw_door_symbol(self, op: Opening, wall_start: tuple, wall_end: tuple):
        """Símbolo de porta conforme padrão arquitetônico:
        - Linha reta da dobradiça até a ponta da folha em posição ABERTA (perpendicular à parede).
        - Arco de varredura da posição fechada (ao longo da parede) à posição aberta (inside).

        A folha é exibida perpendicular à parede (posição aberta), e o arco indica
        o espaço necessário para a abertura — convenção universal em plantas baixas.
        """
        dx = wall_end[0] - wall_start[0]
        dy = wall_end[1] - wall_start[1]
        wall_length = math.hypot(dx, dy)
        ux, uy = dx / wall_length, dy / wall_length

        # Vetor normal inward (90° anti-horário em relação à direção da parede)
        # Para parede S (→): inward = (0, +1) = para cima ✓
        # Para parede N (←): inward = (0, -1) = para baixo ✓
        # Para parede E (↑): inward = (-1, 0) = para esquerda ✓
        # Para parede W (↓): inward = (+1, 0) = para direita ✓
        in_x, in_y = -uy, ux

        wall_angle = math.degrees(math.atan2(dy, dx))
        w = op.width

        if op.swing == 'right':
            # Dobradiça no lado esquerdo da abertura (offset)
            hinge = (
                wall_start[0] + ux * op.offset,
                wall_start[1] + uy * op.offset,
            )
            # Posição aberta: perpendicular à parede, para dentro
            open_end = (hinge[0] + in_x * w, hinge[1] + in_y * w)
            # Arco: de fechado (0° = ao longo da parede) → aberto (+90° = inward)
            arc_start = wall_angle % 360
            arc_end   = (wall_angle + 90) % 360
        else:  # swing == 'left'
            # Dobradiça no lado direito da abertura (offset + width)
            hinge = (
                wall_start[0] + ux * (op.offset + w),
                wall_start[1] + uy * (op.offset + w),
            )
            open_end = (hinge[0] + in_x * w, hinge[1] + in_y * w)
            # Arco: de aberto (+90° = inward) → fechado (+180° = contra a parede)
            arc_start = (wall_angle + 90)  % 360
            arc_end   = (wall_angle + 180) % 360

        # Folha (posição aberta)
        self.msp.add_line(hinge, open_end, dxfattribs={"layer": "PT_DOORS"})

        # Arco de varredura
        self.msp.add_arc(
            hinge,
            radius=w,
            start_angle=arc_start,
            end_angle=arc_end,
            dxfattribs={"layer": "PT_DOORS"},
        )

    def _draw_window_symbol(self, op: Opening, wall_start: tuple, wall_end: tuple):
        """Símbolo de janela: duas linhas paralelas dentro da espessura da parede,
        representando o peitoril e a verga em planta.
        """
        dx = wall_end[0] - wall_start[0]
        dy = wall_end[1] - wall_start[1]
        wall_length = math.hypot(dx, dy)
        ux, uy = dx / wall_length, dy / wall_length
        in_x, in_y = -uy, ux   # normal inward

        inset = 0.04   # distância do face externa até a primeira linha
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
            self.msp.add_line(
                (p_start[0] + ox, p_start[1] + oy),
                (p_end[0]   + ox, p_end[1]   + oy),
                dxfattribs={"layer": "PT_WINDOWS"},
            )

    # ------------------------------------------------------------------
    # Lighting
    # ------------------------------------------------------------------

    def draw_lighting(self, room: BaseRoom):
        """Símbolo de ponto de iluminação no centro do cômodo.

        Convenção de planta baixa elétrica: círculo com X inscrito,
        representando a luminária de teto (ponto de luz).
        """
        x, y = room.origin
        cx = x + room.width  / 2
        cy = y + room.length / 2
        r  = 0.15            # raio do símbolo (metros)
        d  = r / math.sqrt(2)

        self.msp.add_circle(
            (cx, cy), radius=r, dxfattribs={"layer": "PT_LIGHTING"}
        )
        # Diagonais formando o X
        self.msp.add_line(
            (cx - d, cy - d), (cx + d, cy + d),
            dxfattribs={"layer": "PT_LIGHTING"}
        )
        self.msp.add_line(
            (cx + d, cy - d), (cx - d, cy + d),
            dxfattribs={"layer": "PT_LIGHTING"}
        )

    # ------------------------------------------------------------------
    # Appliances / TUGs
    # ------------------------------------------------------------------

    def draw_appliances(self, room: BaseRoom, wall_thickness: float = 0.15):
        """Distribui os pontos de TUG ao longo do perímetro do cômodo.

        Conforme NBR 5410, as tomadas de uso geral devem ser espaçadas por no máximo
        3,5 m de perímetro. Esta função distribui os pontos uniformemente ao redor
        das 4 paredes, na face interna da alvenaria.

        O percurso segue a ordem: Sul → Leste → Norte → Oeste.
        """
        if not room.appliances:
            return

        x, y = room.origin
        w, l = room.width, room.length
        perim   = 2 * (w + l)
        n       = len(room.appliances)
        spacing = perim / n

        for i, app in enumerate(room.appliances):
            # Posição no centro de cada intervalo de spacing
            dist = spacing * i + spacing / 2
            px, py = self._perimeter_point(x, y, w, l, dist, wall_thickness)

            # Símbolo: círculo (TUG)
            self.msp.add_circle(
                (px, py), radius=0.06, dxfattribs={"layer": "PT_SYMBOLS"}
            )
            # Etiqueta de potência
            self.msp.add_text(
                f"{app.wattage}W",
                dxfattribs={"height": 0.1, "layer": "PT_TEXT"}
            ).set_placement((px + 0.07, py + 0.1))

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save(self, filename: str = "output.dxf"):
        self.doc.saveas(filename)
        print(f"Arquivo DXF salvo como '{filename}'")
