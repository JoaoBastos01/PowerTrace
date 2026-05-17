"""Modelo de circuito elétrico conforme NBR 5410."""
from dataclasses import dataclass

from core.electrical.standards.nbr5410 import ElectricalStandards, WireSpec


@dataclass
class CircuitDimension:
    """Resultado do dimensionamento de um circuito."""
    circuit_id:          str
    total_wattage:       int
    current:             float   # corrente real (A)
    design_current:      float   # corrente dimensionada com margem 10% (A)
    breaker:             int     # disjuntor selecionado (A)
    wire:                WireSpec

    def __str__(self):
        return (
            f"[{self.circuit_id}] {self.total_wattage}W | "
            f"I={self.current:.2f}A → {self.design_current:.2f}A (dim.) | "
            f"Disjuntor: {self.breaker}A | Cabo: {self.wire}"
        )


class Circuit:
    """Representa um circuito elétrico com seus pontos de carga.

    Encapsula o cálculo de corrente e o dimensionamento de condutor
    e proteção conforme NBR 5410.
    """

    def __init__(self, circuit_id: str, voltage: int = 127, pf: float = 0.92):
        self.circuit_id  = circuit_id
        self.voltage     = voltage
        self.pf          = pf
        self.load_points = []
        self.description = ""

    def add_load_point(self, load_point) -> None:
        """Adiciona um ponto de carga (Appliance) ao circuito."""
        self.load_points.append(load_point)

    # ------------------------------------------------------------------
    # Propriedades derivadas
    # ------------------------------------------------------------------

    @property
    def total_wattage(self) -> int:
        return sum(lp.wattage for lp in self.load_points)

    @property
    def current(self) -> float:
        """Corrente real de operação (A), sem margem de segurança."""
        if self.total_wattage == 0:
            return 0.0
        return self.total_wattage / (self.voltage * self.pf)

    @property
    def design_current(self) -> float:
        """Corrente dimensionada com margem de 10% (A)."""
        return self.current * 1.10

    # ------------------------------------------------------------------
    # Dimensionamento
    # ------------------------------------------------------------------

    def dimension(self) -> CircuitDimension:
        """Dimensiona o circuito: seleciona disjuntor e bitola do cabo.

        Retorna um CircuitDimension com todos os dados do dimensionamento.

        Levanta:
            ValueError -- se a carga exceder os limites da tabela NBR 5410.
        """
        breaker = ElectricalStandards.select_breaker(self.design_current)
        wire    = ElectricalStandards.select_wire(self.design_current)

        return CircuitDimension(
            circuit_id     = self.circuit_id,
            total_wattage  = self.total_wattage,
            current        = round(self.current, 2),
            design_current = round(self.design_current, 2),
            breaker        = breaker,
            wire           = wire,
        )

    def __repr__(self):
        return (
            f"Circuit(id={self.circuit_id!r}, "
            f"load_points={len(self.load_points)}, "
            f"total={self.total_wattage}W)"
        )
