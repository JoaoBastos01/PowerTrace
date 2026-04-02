"""Tipos de cômodo com regras NBR 5410 específicas."""
import math
from .base import BaseRoom
from .appliances import Appliance, ApplianceType


class Kitchen(BaseRoom):
    """Cozinha conforme NBR 5410.

    Regras aplicadas:
      - TUGs de bancada: mínimo 3 pontos de 600W (uso de eletrodomésticos pesados)
      - TUGs gerais: espaçamento máximo de 3,5m de perímetro
      - 1 ponto de iluminação no teto
    """

    def apply_nbr5410_rules(self) -> None:
        # Quantidade mínima de TUGs pelo perímetro (máx. 3,5m entre pontos)
        qty = math.ceil(self.perimeter / 3.5)

        for i in range(qty):
            # Os 3 primeiros são de bancada (600W), os demais são complementares
            wattage = 600 if i < 3 else 100
            self.add_appliance(Appliance(
                name=f"TUG cozinha {i + 1}",
                wattage=wattage,
                type=ApplianceType.GENERAL,
            ))

        # Ponto de iluminação (obrigatório NBR 5410 item 9.12.3)
        self.add_appliance(Appliance(
            name="Luminária teto",
            wattage=100,
            type=ApplianceType.LIGHTING,
        ))