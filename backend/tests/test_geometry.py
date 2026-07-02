import pytest
import math

from core.drawing.geometry import inward_normal, perimeter_point, wall_unit_vector

# ────────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────────

W, L, T = 4.0, 3.0, 0.15

# dist cumulativa: S=[0,4]  E=[4,7]  N=[7,11]  W=[11,14]
#                              ↑w      ↑w+l       ↑2w+l
S_DIST = 2.0    # 2m na parede S (meio da parede)
E_DIST = 5.0    # 1m na parede E  (4 + 1)
N_DIST = 9.0    # 2m na parede N  (7 + 2)
W_DIST = 12.0   # 1m na parede W  (11 + 1)

# Spans úteis internos (com corner_margin = t por padrão)

IW = W - 2 * T - 2 * T   # = 4 - 0.60 = 3.40
IL = L - 2 * T - 2 * T   # = 3 - 0.60 = 2.40

# ────────────────────────────────────────────────────────────────────
# perimeter_point — posicionamento nas 4 paredes
# ────────────────────────────────────────────────────────────────────

def test_perimeter_point_south_wall():
    """Ponto no meio da parede S: py deve ser t (face interna)."""
    px, py = perimeter_point(0, 0, W, L, dist=S_DIST, t=T)
    expected_x = 0 + T + T + (S_DIST / W) * IW   # offset + margin + fração
    assert py == pytest.approx(T)
    assert px == pytest.approx(expected_x)

def test_perimeter_point_east_wall():
    """Ponto 1m na parede E: px deve ser w-t (face interna direita)."""
    px, py = perimeter_point(0, 0, W, L, dist=E_DIST, t=T)
    dist_within = E_DIST - W   # 1m dentro da parede E
    expected_y = 0 + T + T + (dist_within / L) * IL
    assert px == pytest.approx(W - T)
    assert py == pytest.approx(expected_y)

def test_perimeter_point_north_wall():
    """Ponto no meio da parede N: py deve ser l-t (face interna topo)."""
    px, py = perimeter_point(0, 0, W, L, dist=N_DIST, t=T)
    dist_within = N_DIST - W - L   # 2m dentro da parede N
    expected_x = 0 + W - T - T - (dist_within / W) * IW
    assert py == pytest.approx(L - T)
    assert px == pytest.approx(expected_x)

def test_perimeter_point_west_wall():
    """Ponto 1m na parede W: px deve ser t (face interna esquerda)."""
    px, py = perimeter_point(0, 0, W, L, dist=W_DIST, t=T)
    dist_within = W_DIST - W - L - W   # 1m dentro da parede W
    expected_y = 0 + L - T - T - (dist_within / L) * IL
    assert px == pytest.approx(T)
    assert py == pytest.approx(expected_y)

# ────────────────────────────────────────────────────────────────────
# perimeter_point — garantias de segurança (sempre dentro da face interna)
# ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("dist", [
    0.1, 1.0, 2.0, 3.9,          # parede S
    4.1, 5.0, 6.9,               # parede E
    7.1, 8.0, 9.0, 10.9,         # parede N
    11.1, 12.0, 13.9,            # parede W
])

def test_perimeter_point_always_inside_inner_wall(dist):
    """Nenhum ponto deve ultrapassar a face interna em nenhuma direção."""
    px, py = perimeter_point(0, 0, W, L, dist=dist, t=T)
    assert px >= T - 1e-9,      f"px={px:.4f} fora do limite esquerdo"
    assert px <= W - T + 1e-9,  f"px={px:.4f} fora do limite direito"
    assert py >= T - 1e-9,      f"py={py:.4f} fora do limite inferior"
    assert py <= L - T + 1e-9,  f"py={py:.4f} fora do limite superior"

def test_perimeter_point_wraparound():
    """dist >= perímetro deve fazer wrap e retornar posição equivalente."""
    perim = 2 * (W + L)
    p1 = perimeter_point(0, 0, W, L, dist=1.5, t=T)
    p2 = perimeter_point(0, 0, W, L, dist=1.5 + perim, t=T)
    assert p1[0] == pytest.approx(p2[0])
    assert p1[1] == pytest.approx(p2[1])

def test_perimeter_point_corner_margin_kept():
    """Nenhum ponto deve estar a menos de corner_margin de uma transição de parede."""
    margin = T
    for dist in [0.01, W - 0.01, W + 0.01, W + L - 0.01]:
        px, py = perimeter_point(0, 0, W, L, dist=dist, t=T, corner_margin=margin)
        # O ponto nunca deve cair exatamente nos cantos internos
        is_inner_corner = (
            (px == pytest.approx(T)     and py == pytest.approx(T))     or
            (px == pytest.approx(W - T) and py == pytest.approx(T))     or
            (px == pytest.approx(W - T) and py == pytest.approx(L - T)) or
            (px == pytest.approx(T)     and py == pytest.approx(L - T))
        )
        assert not is_inner_corner, f"Ponto no canto com dist={dist}"

# ────────────────────────────────────────────────────────────────────
# wall_unit_vector
# ────────────────────────────────────────────────────────────────────

def test_wall_unit_vector_horizontal():
    (ux, uy), length = wall_unit_vector((0, 0), (4, 0))
    assert ux == pytest.approx(1.0)
    assert uy == pytest.approx(0.0)
    assert length == pytest.approx(4.0)

def test_wall_unit_vector_vertical():
    (ux, uy), length = wall_unit_vector((0, 0), (0, 3))
    assert ux == pytest.approx(0.0)
    assert uy == pytest.approx(1.0)
    assert length == pytest.approx(3.0)

def test_wall_unit_vector_zero_length():
    """Segmento de comprimento zero não deve lançar exceção."""
    (ux, uy), length = wall_unit_vector((2, 2), (2, 2))
    assert length == pytest.approx(0.0)

# ────────────────────────────────────────────────────────────────────
# inward_normal
# ────────────────────────────────────────────────────────────────────

def test_inward_normal_east_wall():
    """Parede E (↑): normal inward deve apontar para esquerda (−x)."""
    in_x, in_y = inward_normal(0.0, 1.0)
    assert in_x == pytest.approx(-1.0)
    assert in_y == pytest.approx(0.0)

def test_inward_normal_south_wall():
    """Parede S (→): normal inward deve apontar para cima (+y)."""
    in_x, in_y = inward_normal(1.0, 0.0)
    assert in_x == pytest.approx(0.0)
    assert in_y == pytest.approx(1.0)

def test_inward_normal_is_perpendicular():
    """Normal deve ser sempre perpendicular ao vetor da parede (produto escalar = 0)."""
    (ux, uy), _ = wall_unit_vector((1, 1), (4, 3))
    in_x, in_y = inward_normal(ux, uy)
    dot = ux * in_x + uy * in_y
    assert dot == pytest.approx(0.0)


def test_inward_normal_is_unit_vector():
    """Normal deve ter magnitude 1."""
    (ux, uy), _ = wall_unit_vector((0, 0), (3, 4))
    in_x, in_y = inward_normal(ux, uy)
    magnitude = math.hypot(in_x, in_y)
    assert magnitude == pytest.approx(1.0)
