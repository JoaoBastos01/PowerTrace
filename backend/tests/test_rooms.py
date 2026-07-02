import math
import pytest

from core.electrical.appliances import ApplianceType
from core.electrical.circuit import Circuit
from core.electrical.rooms import Kitchen


# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────


def make_kitchen(width=4.0, length=3.0) -> Kitchen:
    """Cria e aplica as regras NBR 5410 em uma Kitchen."""
    k = Kitchen(name="Cozinha Teste", width=width, length=length)
    k.apply_nbr5410_rules()
    return k


# ────────────────────────────────────────────────────────────────────
# BaseRoom — propriedades geométricas
# ────────────────────────────────────────────────────────────────────


def test_area():
    k = Kitchen("K", width=4.0, length=3.0)
    assert k.area == pytest.approx(12.0)


def test_perimeter():
    k = Kitchen("K", width=4.0, length=3.0)
    assert k.perimeter == pytest.approx(14.0)


def test_origin_default():
    """Origin padrão deve ser (0, 0)."""
    k = Kitchen("K", width=4.0, length=3.0)
    assert k.origin == (0, 0)


def test_origin_custom():
    """Origin deve refletir o valor passado."""
    k = Kitchen("K", width=4.0, length=3.0, origin=(5.0, 3.0))
    assert k.origin == (5.0, 3.0)


# ────────────────────────────────────────────────────────────────────
# Kitchen — apply_nbr5410_rules
# ────────────────────────────────────────────────────────────────────


def test_kitchen_has_appliances_after_rules():
    """Após apply_nbr5410_rules, a lista não deve estar vazia."""
    k = make_kitchen()
    assert len(k.appliances) > 0


def test_kitchen_has_lighting():
    """Deve ter ao menos 1 ponto de iluminação."""
    k = make_kitchen()
    lighting = [a for a in k.appliances if a.type == ApplianceType.LIGHTING]
    assert len(lighting) >= 1


def test_kitchen_has_general_tugs():
    """Deve ter ao menos 1 TUG geral."""
    k = make_kitchen()
    general = [a for a in k.appliances if a.type == ApplianceType.GENERAL]
    assert len(general) >= 1


def test_kitchen_tug_spacing_nbr5410():
    """Quantidade de TUGs deve ser ceil(perimetro / 3.5)."""
    k = Kitchen("K", width=4.0, length=3.0)
    expected_tugs = math.ceil(k.perimeter / 3.5)
    k.apply_nbr5410_rules()
    general = [a for a in k.appliances if a.type == ApplianceType.GENERAL]
    assert len(general) == expected_tugs


def test_kitchen_first_three_tugs_are_600w():
    """Os 3 primeiros TUGs (bancada) devem ter 600W."""
    k = make_kitchen(width=10.0, length=5.0)  # grande o suficiente para >= 3 TUGs
    general = [a for a in k.appliances if a.type == ApplianceType.GENERAL]
    for tug in general[:3]:
        assert tug.wattage == 600


def test_kitchen_remaining_tugs_are_100w():
    """TUGs além dos 3 primeiros devem ter 100W."""
    k = make_kitchen(width=10.0, length=5.0)  # muitos TUGs
    general = [a for a in k.appliances if a.type == ApplianceType.GENERAL]
    for tug in general[3:]:
        assert tug.wattage == 100


def test_kitchen_rules_currently_append_on_reapplication():
    """Documenta que a reaplicação atual acrescenta novamente as cargas."""
    k = Kitchen("K", width=4.0, length=3.0)
    k.apply_nbr5410_rules()
    count_first = len(k.appliances)
    k.apply_nbr5410_rules()
    assert len(k.appliances) == count_first * 2


def test_kitchen_get_total_wattage():
    """Total de wattage deve ser a soma de todos os appliances."""
    k = make_kitchen()
    expected = sum(a.wattage for a in k.appliances)
    assert k.get_total_wattage() == expected


# ────────────────────────────────────────────────────────────────────
# BaseRoom — build_circuits
# ────────────────────────────────────────────────────────────────────


def test_build_circuits_returns_list():
    """build_circuits deve retornar uma lista."""
    k = make_kitchen()
    assert isinstance(k.build_circuits(), list)


def test_build_circuits_returns_circuit_instances():
    """Cada elemento da lista deve ser um Circuit."""
    k = make_kitchen()
    for c in k.build_circuits():
        assert isinstance(c, Circuit)


def test_kitchen_has_lighting_circuit():
    """Kitchen com luminária deve gerar um circuito de iluminação."""
    k = make_kitchen()
    ids = [c.circuit_id for c in k.build_circuits()]
    assert any("LUZ" in cid for cid in ids)


def test_kitchen_has_tug_circuit():
    """Kitchen deve gerar um circuito de TUGs gerais."""
    k = make_kitchen()
    ids = [c.circuit_id for c in k.build_circuits()]
    assert any("TUG" in cid for cid in ids)


def test_build_circuits_no_empty_circuits():
    """Nenhum circuito gerado deve ter total_wattage == 0."""
    k = make_kitchen()
    for c in k.build_circuits():
        assert c.total_wattage > 0, f"Circuito {c.circuit_id} está vazio"


def test_build_circuits_dedicated_one_per_appliance():
    """Cada appliance DEDICATED deve gerar seu próprio circuito."""
    from core.electrical.appliances import Appliance

    k = Kitchen("K", width=4.0, length=3.0)
    k.add_appliance(Appliance("Forno", 3000, type=ApplianceType.DEDICATED))
    k.add_appliance(Appliance("Ar cond", 1500, type=ApplianceType.DEDICATED))
    circuits = k.build_circuits()
    dedicated = [c for c in circuits if "FORNO" in c.circuit_id or "AR" in c.circuit_id]
    assert len(dedicated) == 2


def test_build_circuits_voltage_matches_room():
    """Circuitos devem herdar a tensão do cômodo."""
    k = Kitchen("K", width=4.0, length=3.0, voltage=220)
    k.apply_nbr5410_rules()
    for c in k.build_circuits():
        assert c.voltage == 220


def test_build_circuits_all_dimensionable():
    """Todos os circuitos da Kitchen devem ser dimensionáveis sem erro."""
    k = make_kitchen()
    for c in k.build_circuits():
        dim = c.dimension()  # não deve lançar ValueError
        assert dim is not None
