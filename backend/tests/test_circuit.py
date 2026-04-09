import pytest
from models.circuit import Circuit, CircuitDimension
from models.appliances import Appliance
from standards.nbr5410 import WireSpec


# ────────────────────────────────────────────────────────────────────
# Helpers — appliances reutilizáveis nos testes
# ────────────────────────────────────────────────────────────────────

def make_appliance(wattage: int) -> Appliance:
    return Appliance(name=f"Carga {wattage}W", wattage=wattage)

def make_circuit(wattages: list[int], voltage=127, pf=0.92) -> Circuit:
    """Cria um Circuit já populado com appliances."""
    c = Circuit("TEST", voltage=voltage, pf=pf)
    for w in wattages:
        c.add_load_point(make_appliance(w))
    return c


# ────────────────────────────────────────────────────────────────────
# total_wattage
# ────────────────────────────────────────────────────────────────────

def test_total_wattage_empty_circuit():
    """Circuito sem cargas → 0W."""
    c = Circuit("VAZIO")
    assert c.total_wattage == 0

def test_total_wattage_single_load():
    """Um único appliance → wattage dele."""
    c = make_circuit([600])
    assert c.total_wattage == 600

def test_total_wattage_multiple_loads():
    """Soma correta de múltiplas cargas."""
    c = make_circuit([600, 600, 100])
    assert c.total_wattage == 1300

def test_total_wattage_updates_after_add():
    """Wattage deve refletir novo ponto de carga adicionado depois."""
    c = Circuit("DYN")
    c.add_load_point(make_appliance(500))
    assert c.total_wattage == 500
    c.add_load_point(make_appliance(300))
    assert c.total_wattage == 800


# ────────────────────────────────────────────────────────────────────
# current / design_current
# ────────────────────────────────────────────────────────────────────

def test_current_empty_circuit_is_zero():
    """Circuito vazio → corrente 0A (não divide por zero)."""
    c = Circuit("VAZIO")
    assert c.current == pytest.approx(0.0)

def test_current_formula():
    """I = P / (V * PF) — valor exato verificável."""
    # 127V * 0.92 * 10A = 1168.4W → usamos 1168.4W
    c = make_circuit([1168], voltage=127, pf=1.0)
    # 1168 / (127 * 1.0) ≈ 9.197A
    assert c.current == pytest.approx(1168 / (127 * 1.0), rel=1e-4)

def test_design_current_is_10_percent_above_current():
    """Corrente dimensionada deve ser exatamente 10% acima da real."""
    c = make_circuit([1000])
    assert c.design_current == pytest.approx(c.current * 1.10, rel=1e-6)

def test_design_current_always_greater_than_current():
    """design_current > current para qualquer carga não-nula."""
    c = make_circuit([600, 600, 100])
    assert c.design_current > c.current

def test_higher_voltage_lower_current():
    """Tensão maior → corrente menor para mesma carga."""
    c_127 = make_circuit([1000], voltage=127)
    c_220 = make_circuit([1000], voltage=220)
    assert c_220.current < c_127.current

def test_lower_pf_higher_current():
    """Fator de potência menor → corrente maior para mesma carga."""
    c_high_pf = make_circuit([1000], pf=1.0)
    c_low_pf  = make_circuit([1000], pf=0.8)
    assert c_low_pf.current > c_high_pf.current


# ────────────────────────────────────────────────────────────────────
# dimension()
# ────────────────────────────────────────────────────────────────────

def test_dimension_returns_circuit_dimension():
    """dimension() deve retornar uma instância de CircuitDimension."""
    c = make_circuit([600])
    assert isinstance(c.dimension(), CircuitDimension)

def test_dimension_circuit_id_preserved():
    """CircuitDimension deve preservar o circuit_id original."""
    c = Circuit("C01_TUG")
    c.add_load_point(make_appliance(600))
    assert c.dimension().circuit_id == "C01_TUG"

def test_dimension_total_wattage_preserved():
    """CircuitDimension deve ter o mesmo total_wattage do circuito."""
    c = make_circuit([600, 600, 100])
    dim = c.dimension()
    assert dim.total_wattage == c.total_wattage

def test_dimension_wire_is_wirespec():
    """Campo wire do CircuitDimension deve ser WireSpec."""
    c = make_circuit([600])
    assert isinstance(c.dimension().wire, WireSpec)

def test_dimension_breaker_covers_design_current():
    """Invariante: disjuntor >= corrente dimensionada (In >= Ib)."""
    c = make_circuit([600, 600, 100])
    dim = c.dimension()
    assert dim.breaker >= dim.design_current

def test_dimension_wire_covers_breaker():
    """Invariante: cabo suporta o disjuntor (Iz >= In)."""
    c = make_circuit([600, 600, 100])
    dim = c.dimension()
    assert dim.wire.max_current >= dim.breaker

@pytest.mark.parametrize("wattages", [
    [100],
    [600],
    [600, 600],
    [600, 600, 600, 100, 100],
])
def test_dimension_invariants_for_various_loads(wattages):
    """Para qualquer carga: In >= Ib e Iz >= In devem ser sempre verdadeiros."""
    c = make_circuit(wattages)
    dim = c.dimension()
    assert dim.breaker        >= dim.design_current, "In < Ib"
    assert dim.wire.max_current >= dim.breaker,      "Iz < In"

def test_dimension_empty_circuit_uses_minimum_breaker():
    """Circuito vazio (0A) → disjuntor mínimo de 10A."""
    c = Circuit("VAZIO")
    dim = c.dimension()
    assert dim.breaker == 10
