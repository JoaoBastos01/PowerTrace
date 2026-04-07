import pytest
from standards.nbr5410 import ElectricalStandards, WireSpec


# ────────────────────────────────────────────────────────────────────
# select_breaker
# ────────────────────────────────────────────────────────────────────
def test_select_breaker_below_minimum():
    """Corrente abaixo do menor disjuntor → retorna o menor (10A)."""
    assert ElectricalStandards.select_breaker(8.0) == 10


def test_select_breaker_exact_minimum():
    """Corrente exatamente no menor disjuntor → retorna ele mesmo."""
    assert ElectricalStandards.select_breaker(10.0) == 10


def test_select_breaker_just_above_minimum():
    """Corrente logo acima de 10A → sobe para 16A."""
    assert ElectricalStandards.select_breaker(10.1) == 16


def test_select_breaker_exact_mid():
    """Corrente exata em um disjuntor intermediário."""
    assert ElectricalStandards.select_breaker(25.0) == 25


def test_select_breaker_just_above_mid():
    """Corrente logo acima de 25A → sobe para 32A."""
    assert ElectricalStandards.select_breaker(25.1) == 32


def test_select_breaker_exact_maximum():
    """Corrente exatamente no maior disjuntor → retorna 100A."""
    assert ElectricalStandards.select_breaker(100.0) == 100


def test_select_breaker_overflow_raises():
    """Corrente acima do maior disjuntor → ValueError."""
    with pytest.raises(ValueError):
        ElectricalStandards.select_breaker(100.1)


def test_select_breaker_far_overflow_raises():
    """Corrente muito acima do limite → ValueError."""
    with pytest.raises(ValueError):
        ElectricalStandards.select_breaker(999.0)


@pytest.mark.parametrize(
    "current,expected",
    [
        (1.0, 10),
        (10.0, 10),
        (16.0, 16),
        (20.0, 20),
        (32.0, 32),
        (50.0, 50),
        (63.0, 63),
    ],
)
def test_select_breaker_table_values(current, expected):
    """Valores exatos da tabela de disjuntores comerciais."""
    assert ElectricalStandards.select_breaker(current) == expected


# ────────────────────────────────────────────────────────────────────
# select_wire
# ────────────────────────────────────────────────────────────────────
def test_select_wire_returns_wirespec():
    """Resultado deve ser uma instância de WireSpec."""
    result = ElectricalStandards.select_wire(8.0)
    assert isinstance(result, WireSpec)


def test_select_wire_minimum_gauge():
    """Corrente baixa → bitola mínima 1.5mm²."""
    wire = ElectricalStandards.select_wire(8.0)
    assert wire.gauge_mm2 == 1.5


def test_select_wire_higher_current_gives_larger_gauge():
    """Corrente maior deve resultar em bitola maior ou igual."""
    wire_low = ElectricalStandards.select_wire(10.0)
    wire_high = ElectricalStandards.select_wire(30.0)
    assert wire_high.gauge_mm2 >= wire_low.gauge_mm2


def test_select_wire_overflow_raises():
    """Corrente acima da tabela → ValueError."""
    with pytest.raises(ValueError):
        ElectricalStandards.select_wire(999.0)


@pytest.mark.parametrize(
    "design_current", [5.0, 8.0, 10.0, 15.0, 20.0, 25.0, 35.0, 50.0, 80.0, 100.0]
)
def test_select_wire_iz_always_gte_breaker(design_current):
    """Invariante NBR 5410: Iz >= In — cabo deve sempre suportar o disjuntor."""
    wire = ElectricalStandards.select_wire(design_current)
    breaker = ElectricalStandards.select_breaker(design_current)
    assert wire.max_current >= breaker, (
        f"Iz={wire.max_current}A < In={breaker}A para I_dim={design_current}A"
    )


def test_select_wire_has_positive_resistance():
    """Toda bitola da tabela deve ter resistência positiva."""
    wire = ElectricalStandards.select_wire(8.0)
    assert wire.resistance > 0


def test_select_wire_larger_gauge_lower_resistance():
    """Bitola maior deve ter resistência por km menor (lei física)."""
    wire_small = ElectricalStandards.select_wire(10.0)  # 1.5mm²
    wire_large = ElectricalStandards.select_wire(50.0)  # bitola maior
    assert wire_large.resistance < wire_small.resistance


# ────────────────────────────────────────────────────────────────────
# calculate_gauge
# ────────────────────────────────────────────────────────────────────
def test_calculate_gauge_returns_dict():
    """Retorno deve ser um dicionário."""
    result = ElectricalStandards.calculate_gauge(1000, 127)
    assert isinstance(result, dict)


def test_calculate_gauge_has_required_keys():
    """Dict deve conter as 4 chaves obrigatórias."""
    result = ElectricalStandards.calculate_gauge(1000, 127)
    assert "corrente" in result
    assert "corrente_dimensionada" in result
    assert "disjuntor" in result
    assert "cabo" in result


def test_calculate_gauge_cabo_is_wirespec():
    """Campo 'cabo' deve ser uma instância de WireSpec."""
    result = ElectricalStandards.calculate_gauge(1000, 127)
    assert isinstance(result["cabo"], WireSpec)


def test_calculate_gauge_design_current_has_10_percent_margin():
    """Corrente dimensionada deve ser 10% maior que a real."""
    result = ElectricalStandards.calculate_gauge(1000, 127)
    assert result["corrente_dimensionada"] == pytest.approx(
        result["corrente"] * 1.10, rel=1e-3
    )


def test_calculate_gauge_current_always_below_design():
    """Corrente real sempre menor que a dimensionada."""
    result = ElectricalStandards.calculate_gauge(1000, 127)
    assert result["corrente"] < result["corrente_dimensionada"]


def test_calculate_gauge_current_calculation():
    """I = P / (V * PF) — valor exato verificável."""
    # 1270W / (127V * 1.0) = 10.0A exato
    result = ElectricalStandards.calculate_gauge(load=1270, voltage=127, pf=1.0)
    assert result["corrente"] == pytest.approx(10.0)


def test_calculate_gauge_pf_affects_current():
    """Fator de potência menor → corrente maior para mesma carga."""
    result_pf1 = ElectricalStandards.calculate_gauge(1000, 127, pf=1.0)
    result_pf09 = ElectricalStandards.calculate_gauge(1000, 127, pf=0.9)
    assert result_pf09["corrente"] > result_pf1["corrente"]


def test_calculate_gauge_higher_voltage_lower_current():
    """Tensão maior → corrente menor para mesma potência (lei de Ohm)."""
    result_127 = ElectricalStandards.calculate_gauge(1000, 127)
    result_220 = ElectricalStandards.calculate_gauge(1000, 220)
    assert result_220["corrente"] < result_127["corrente"]
