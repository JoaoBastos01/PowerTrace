"""Room types with specific NBR 5410/8995-1 rules."""

import math
from .base import BaseRoom
from .appliances import Appliance, ApplianceType
from standards.nbr8995 import lighting_calculator


class Kitchen(BaseRoom):
    """Kitchen according to NBR 5410 and NBR 8995-1.
    Rules applied:
      - Luminaires: Lumen Method (NBR 8995) — 300 lux required
      - Countertop outlets: minimum 3 points of 600W
      - General outlets: maximum spacing of 3.5m of perimeter (NBR 5410)
    """

    ROOM_TYPE = "kitchen"

    def apply_nbr5410_rules(self) -> None:
        self._apply_lighting()
        self._apply_tugs()

    def _apply_lighting(self) -> None:
        """Lighting calculated by the Lumen Method (NBR 8995)."""
        result = lighting_calculator(self.ROOM_TYPE, self.area, self.width, self.length)
        wattage_each = int(result.total_power_w / result.fixture_count)
        for i in range(result.fixture_count):
            self.add_appliance(
                Appliance(
                    name=f"Luminária {i + 1}",
                    wattage=wattage_each,
                    type=ApplianceType.LIGHTING,
                )
            )

    def _apply_tugs(self) -> None:
        """TUGs distributed along the perimeter, max. 3.5m between points (NBR 5410)."""
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
