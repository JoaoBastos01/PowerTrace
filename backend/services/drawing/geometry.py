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
                    dist: float, t: float = 0.15) -> tuple:
    """Converte uma distância ao longo do perímetro em coordenada (px, py).

    O caminho percorre as paredes em ordem: S → E → N → W.
    O ponto resultante é deslocado `t` metros para dentro do cômodo,
    ficando encostado na face interna da parede (posição padrão de TUGs
    conforme NBR 5410).

    Parâmetros:
        x, y  -- Origem (canto SW) do cômodo.
        w, l  -- Largura e comprimento.
        dist  -- Distância ao longo do perímetro, em metros.
        t     -- Deslocamento inward (espessura da parede).
    """
    perim = 2 * (w + l)
    dist = dist % perim

    if dist <= w:                           # Parede S: esquerda → direita
        return (x + dist, y + t)
    dist -= w
    if dist <= l:                           # Parede E: baixo → cima
        return (x + w - t, y + dist)
    dist -= l
    if dist <= w:                           # Parede N: direita → esquerda
        return (x + w - dist, y + l - t)
    dist -= w
    return (x + t, y + l - dist)           # Parede W: cima → baixo
