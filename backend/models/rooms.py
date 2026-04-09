"""Room types with specific NBR 5410/8995-1 rules."""

import math
from .base import BaseRoom
from .appliances import Appliance, ApplianceType
from standards.nbr8995 import lighting_calculator


class Kitchen(BaseRoom):
    """Cozinha conforme NBR 5410 e NBR 8995.
    Regras aplicadas:
      - Luminárias: Método dos Lúmens (NBR 8995) — 500 lux exigidos
      - TUGs de bancada: mínimo 3 pontos de 600W
      - TUGs gerais: espaçamento máximo de 3,5m de perímetro (NBR 5410)
    """

    ROOM_TYPE = "kitchen"

    def apply_nbr5410_rules(self) -> None:
        self._apply_lighting()
        self._apply_tugs()

    def _apply_lighting(self) -> None:
        """Luminárias calculadas pelo Método dos Lúmens (NBR 8995)."""
        resultado = lighting_calculator(self.ROOM_TYPE, self.area, self.width, self.length)
        wattage_each = int(resultado.potencia_total_w / resultado.num_luminárias)
        for i in range(resultado.num_luminárias):
            self.add_appliance(
                Appliance(
                    name=f"Luminária {i + 1}",
                    wattage=wattage_each,
                    type=ApplianceType.LIGHTING,
                )
            )

    def _apply_tugs(self) -> None:
        """TUGs distribuídas pelo perímetro, máx. 3,5m entre pontos (NBR 5410)."""
        qty = math.ceil(self.perimeter / 3.5)
        for i in range(qty):
            wattage = 600 if i < 3 else 100  # 3 primeiros são de bancada
            self.add_appliance(
                Appliance(
                    name=f"TUG cozinha {i + 1}",
                    wattage=wattage,
                    type=ApplianceType.GENERAL,
                )
            )
