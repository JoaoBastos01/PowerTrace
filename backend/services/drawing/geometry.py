"""Funções de geometria pura para a drawing engine.

Sem dependências do ezdxf — totalmente testável em isolamento.
"""
import math


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
