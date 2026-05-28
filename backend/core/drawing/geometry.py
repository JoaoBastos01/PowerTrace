"""Funções de geometria pura para a drawing engine.

Sem dependências do ezdxf — totalmente testável em isolamento.
"""
import math
from typing import List, Tuple


def __getattr__(name: str):
    if name == "DXFGenerator":
        from .engine import DXFGenerator

        return DXFGenerator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def wall_unit_vector(p1: tuple, p2: tuple) -> tuple:
    """Retorna o vetor unitário e o comprimento de um segmento de parede.

    Parâmetros:
        p1, p2 -- extremidades do segmento.

    Retorna:
        ((ux, uy), length) -- vetor unitário e comprimento em metros.
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return (0.0, 0.0), 0.0
    return (dx / length, dy / length), length


def inward_normal(ux: float, uy: float) -> tuple:
    """Vetor normal apontando para o interior do cômodo (90° anti-horário).

    Convenções:
        Parede S (→): inward = (0, +1) ↑
        Parede N (←): inward = (0, -1) ↓
        Parede E (↑): inward = (-1, 0) ←
        Parede W (↓): inward = (+1, 0) →
    """
    return (-uy, ux)


def perimeter_point(x: float, y: float, w: float, l: float,
                    dist: float, t: float = 0.15,
                    corner_margin: float = None) -> tuple:
    """Converte uma distância ao longo do perímetro em coordenada (px, py).

    O caminho percorre as paredes em ordem: S → E → N → W.
    O ponto resultante é deslocado `t` metros para dentro do cômodo,
    ficando encostado na face interna da parede (posição padrão de TUGs
    conforme NBR 5410).

    Parâmetros:
        x, y          -- Origem (canto SW) do cômodo.
        w, l          -- Largura e comprimento.
        dist          -- Distância ao longo do perímetro, em metros.
        t             -- Deslocamento inward (espessura da parede).
        corner_margin -- Distância mínima de cada canto (padrão = t).
                         Garante que nenhuma tomada fique exatamente no
                         vértice interno. Não viola a NBR 5410 pois o
                         espaçamento máximo entre tomadas (3,5m) continua
                         sendo respeitado pela distribuição no perímetro.
    """
    if corner_margin is None:
        corner_margin = t   # usar a espessura da parede como margem padrão

    perim = 2 * (w + l)
    dist  = dist % perim

    # Span útil de cada parede: entre os cantos internos, com recuo adicional
    iw = w - 2 * t - 2 * corner_margin   # span horizontal útil
    il = l - 2 * t - 2 * corner_margin   # span vertical útil

    if dist <= w:                                         # Parede S: esquerda → direita
        return (x + t + corner_margin + (dist / w) * iw,   y + t)
    dist -= w
    if dist <= l:                                         # Parede E: baixo → cima
        return (x + w - t,   y + t + corner_margin + (dist / l) * il)
    dist -= l
    if dist <= w:                                         # Parede N: direita → esquerda
        return (x + w - t - corner_margin - (dist / w) * iw, y + l - t)
    dist -= w
    return (x + t,   y + l - t - corner_margin - (dist / l) * il)  # Parede W: cima → baixo


# ---------------------------------------------------------------------------
# Zonas proibidas para tomadas (aberturas)
# ---------------------------------------------------------------------------

def _wall_base(wall: str, width: float, length: float) -> float:
    """Retorna o offset acumulado no perímetro onde cada parede começa.

    Ordem de travessia: S → E → N → W (mesma de perimeter_point).
    """
    return {
        'S': 0.0,
        'E': width,
        'N': width + length,
        'W': 2.0 * width + length,
    }[wall]


def opening_to_perimeter_interval(
    wall: str, offset: float, op_width: float,
    room_width: float, room_length: float,
    margin: float = 0.20,
) -> Tuple[float, float]:
    """Converte uma abertura em intervalo proibido no espaço do perímetro.

    O `offset` de um Opening segue a convenção de walls.py: distância em
    metros desde o canto inicial da parede (S→, E↑, N←, W↓) até o início
    da abertura — exatamente o mesmo sistema de perimeter_point.

    Parâmetros:
        wall        -- Parede onde a abertura está: 'S', 'E', 'N' ou 'W'.
        offset      -- Distância do canto inicial até o início da abertura (m).
        op_width    -- Largura da abertura (m).
        room_width  -- Largura do cômodo (m).
        room_length -- Comprimento do cômodo (m).
        margin      -- Folga de segurança além das bordas da abertura (m).

    Retorna:
        (d_start, d_end) -- Intervalo proibido no perímetro acumulado.
    """
    base = _wall_base(wall, room_width, room_length)
    return (base + offset - margin, base + offset + op_width + margin)


def build_free_segments(
    perim: float,
    forbidden: List[Tuple[float, float]],
) -> List[Tuple[float, float]]:
    """Retorna os segmentos livres do perímetro após excluir as zonas proibidas.

    Parâmetros:
        perim     -- Comprimento total do perímetro (m).
        forbidden -- Lista de (start, end) proibidos. Podem se sobrepor.

    Retorna:
        Lista ordenada de (start, end) de segmentos livres.
    """
    if not forbidden:
        return [(0.0, perim)]

    # Restringe ao intervalo [0, perim] e remove intervalos vazios
    cleaned = sorted(
        (max(0.0, s), min(perim, e))
        for s, e in forbidden
        if s < perim and e > 0.0 and s < e
    )

    if not cleaned:
        return [(0.0, perim)]

    # Merge de intervalos proibidos sobrepostos
    merged: List[List[float]] = [list(cleaned[0])]
    for s, e in cleaned[1:]:
        if s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])

    # Subtrai os intervalos proibidos de [0, perim]
    free: List[Tuple[float, float]] = []
    cursor = 0.0
    for s, e in merged:
        if cursor < s:
            free.append((cursor, s))
        cursor = e
    if cursor < perim:
        free.append((cursor, perim))

    return free if free else [(0.0, perim)]


def map_free_to_absolute(
    dist_free: float,
    free_segments: List[Tuple[float, float]],
) -> float:
    """Converte uma distância no espaço livre para distância absoluta no perímetro.

    Itera sobre os segmentos livres consumindo a distância solicitada.
    Se dist_free exceder o comprimento total livre, retorna o fim do último
    segmento (clamp).

    Parâmetros:
        dist_free     -- Distância medida apenas dentro dos segmentos livres.
        free_segments -- Lista ordenada de (start, end) de segmentos livres.

    Retorna:
        Distância absoluta no perímetro acumulado.
    """
    for seg_start, seg_end in free_segments:
        span = seg_end - seg_start
        if dist_free <= span:
            return seg_start + dist_free
        dist_free -= span
    return free_segments[-1][1]  # clamp
