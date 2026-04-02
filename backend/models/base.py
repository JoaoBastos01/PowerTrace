"""Modelo base para todos os cômodos do PowerTrace."""
from abc import ABC, abstractmethod
from typing import List

from .appliances import Appliance, ApplianceType


class BaseRoom(ABC):
    """Cômodo genérico com dimensões, cargas e geração de circuitos NBR 5410."""

    def __init__(self, name: str, width: float, length: float,
                 voltage: int = 127, origin: tuple = (0, 0)):
        self.name      = name
        self.width     = width
        self.length    = length
        self.voltage   = voltage
        self.origin    = origin
        self.appliances: List[Appliance] = []

    # ------------------------------------------------------------------
    # Propriedades geométricas
    # ------------------------------------------------------------------

    @property
    def area(self) -> float:
        return self.width * self.length

    @property
    def perimeter(self) -> float:
        return 2 * (self.width + self.length)

    # ------------------------------------------------------------------
    # Gestão de cargas
    # ------------------------------------------------------------------

    def add_appliance(self, appliance: Appliance) -> None:
        self.appliances.append(appliance)

    def get_total_wattage(self) -> int:
        return sum(a.wattage for a in self.appliances)

    # ------------------------------------------------------------------
    # NBR 5410
    # ------------------------------------------------------------------

    @abstractmethod
    def apply_nbr5410_rules(self) -> None:
        """Aplica as regras NBR 5410 específicas para este tipo de cômodo.

        Cada subclasse deve preencher `self.appliances` com os pontos
        de carga exigidos pela norma (TUGs, iluminação, dedicados).
        """

    def build_circuits(self) -> list:
        """Agrupa os appliances em circuitos conforme NBR 5410.

        Regras de agrupamento:
          - LIGHTING   → 1 circuito de iluminação por cômodo
          - GENERAL    → 1 circuito de TUGs gerais por cômodo
          - DEDICATED  → 1 circuito exclusivo por carga dedicada

        Retorna:
            Lista de Circuit já populados, prontos para dimensionamento.
        """
        from .circuit import Circuit  # import local para evitar ciclo

        circuits = []

        # ── Iluminação ────────────────────────────────────────────────
        lighting = [a for a in self.appliances if a.type == ApplianceType.LIGHTING]
        if lighting:
            c = Circuit(f"{self.name}_LUZ", voltage=self.voltage)
            for a in lighting:
                c.add_load_point(a)
            circuits.append(c)

        # ── TUGs gerais ───────────────────────────────────────────────
        general = [a for a in self.appliances if a.type == ApplianceType.GENERAL]
        if general:
            c = Circuit(f"{self.name}_TUG", voltage=self.voltage)
            for a in general:
                c.add_load_point(a)
            circuits.append(c)

        # ── Circuitos dedicados (um por carga) ────────────────────────
        dedicated = [a for a in self.appliances if a.type == ApplianceType.DEDICATED]
        for a in dedicated:
            c = Circuit(
                f"{self.name}_{a.name.upper().replace(' ', '_')}",
                voltage=self.voltage
            )
            c.add_load_point(a)
            circuits.append(c)

        return circuits

    # ------------------------------------------------------------------
    # Representação
    # ------------------------------------------------------------------

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"name={self.name}, "
            f"area={self.area}m², "
            f"voltage={self.voltage}V, "
            f"appliances={len(self.appliances)})"
        )