"""Room types with specific NBR 5410/8995-1 rules."""

import math
from .base import BaseRoom
from .appliances import Appliance, ApplianceType, ApplianceSource
from .standards.nbr8995 import lighting_calculator


class Kitchen(BaseRoom):
    """
    Rules applied:
      - Lighting: Lumen Method (NBR 8995) — 300 lux required
      - General outlets: minimum 3 points of 600W, after that 100W per outlet, and maximum spacing of 3.5m of perimeter (NBR 5410)
      - Dedicated outlets: 1 for electric faucet (5500 W, 220 V)
    """

    ROOM_TYPE = "kitchen"

    def apply_nbr5410_rules(self) -> None:
        self._apply_lighting()
        self._apply_tugs()
        self._apply_faucet()

    def _apply_lighting(self) -> None:
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
        qty = math.ceil(self.perimeter / 3.5)
        for i in range(qty):
            wattage = 600 if i < 3 else 100
            self.add_appliance(
                Appliance(
                    name=f"TUG cozinha {i + 1}",
                    wattage=wattage,
                    type=ApplianceType.GENERAL,
                )
            )

    def _apply_faucet(self) -> None:
        self.add_appliance(
            Appliance(
                key="kitchen_electric_faucet",
                name="Torneira elétrica",
                wattage=5500,
                type=ApplianceType.DEDICATED,
                voltage=220,
                source=ApplianceSource.DEFAULT,
            )
        )


class Bedroom(BaseRoom):
    """
    Rules applied:
      - Lighting: Lumen Method (NBR 8995) — 100 lux required
      - General outlets: maximum spacing of 3.5m of perimeter (NBR 5410)
    """

    ROOM_TYPE = "bedroom"

    def apply_nbr5410_rules(self) -> None:
        self._apply_lighting()
        self._apply_tugs()

    def _apply_lighting(self) -> None:
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
        qty = max(1, math.ceil(self.perimeter / 3.5))
        for i in range(qty):
            self.add_appliance(
                Appliance(
                    name=f"TUG quarto {i + 1}",
                    wattage=100,
                    type=ApplianceType.GENERAL,
                )
            )


class Bathroom(BaseRoom):
    """
    Rules applied:
      - Lighting: Lumen Method (NBR 8995) — 100 lux required
      - General outlets: 1 waterproof outlet (protection class IPX4) near the sink
      - Dedicated outlets: 1 for electric shower (5500 W, 220 V)
    """

    ROOM_TYPE = "bathroom"

    def apply_nbr5410_rules(self) -> None:
        self._apply_lighting()
        self._apply_tugs()
        self._apply_shower()

    def _apply_lighting(self) -> None:
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
        self.add_appliance(
            Appliance(
                name="TUG banheiro (IPX4)", wattage=100, type=ApplianceType.GENERAL
            )
        )

    def _apply_shower(self) -> None:
        self.add_appliance(
            Appliance(
                key="bathroom_electric_shower",
                name="Chuveiro elétrico",
                wattage=5500,
                type=ApplianceType.DEDICATED,
                voltage=220,
                source=ApplianceSource.DEFAULT,
            )
        )


class BathroomSocial(BaseRoom):
    """Banheiro social (meio-banheiro) — acessível pela área social.

    Rules applied:
      - Lighting: Lumen Method (NBR 8995) — 100 lux required
      - General outlets: 1 waterproof outlet (IPX4) near the sink
      - No electric shower (half-bath: sink + toilet only)
    """

    ROOM_TYPE = "bathroom_social"

    def apply_nbr5410_rules(self) -> None:
        self._apply_lighting()
        self._apply_tugs()

    def _apply_lighting(self) -> None:
        result = lighting_calculator("bathroom", self.area, self.width, self.length)
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
        self.add_appliance(
            Appliance(
                name="TUG banheiro social (IPX4)",
                wattage=100,
                type=ApplianceType.GENERAL,
            )
        )


class Living(BaseRoom):
    """
    Rules applied:
      - Lighting: Lumen Method (NBR 8995) — 200 lux required
      - General outlets: maximum spacing of 3.5m of perimeter (NBR 5410)
    """

    ROOM_TYPE = "living"

    def apply_nbr5410_rules(self) -> None:
        self._apply_lighting()
        self._apply_tugs()

    def _apply_lighting(self) -> None:
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
        qty = max(2, math.ceil(self.perimeter / 3.5))
        for i in range(qty):
            self.add_appliance(
                Appliance(
                    name=f"TUG sala {i + 1}",
                    wattage=100,
                    type=ApplianceType.GENERAL,
                )
            )


class Corridor(BaseRoom):
    """
    Rules applied:
      - Lighting: Lumen Method (NBR 8995) — 100 lux required
      - General outlets: Not required by NBR 5410, but recommended 1 every 5m of perimeter
    """

    ROOM_TYPE = "corridor"

    def apply_nbr5410_rules(self) -> None:
        self._apply_lighting()

    def _apply_lighting(self) -> None:
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


class Garage(BaseRoom):
    """
    Rules applied:
      - Lighting: Lumen Method (NBR 8995) — 100 lux required
      - General outlets: 1 general outlet (200 W — tools)
      - Dedicated circuits: 1 for automatic gate (300 W)
    """

    ROOM_TYPE = "garage"

    def apply_nbr5410_rules(self) -> None:
        self._apply_lighting()
        self._apply_tugs()
        self._apply_gate()

    def _apply_lighting(self) -> None:
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
        self.add_appliance(
            Appliance(
                name="TUG garagem (ferramentas)",
                wattage=200,
                type=ApplianceType.GENERAL,
            )
        )

    def _apply_gate(self) -> None:
        self.add_appliance(
            Appliance(
                key="garage_gate_motor",
                name="Motor do portão",
                wattage=300,
                type=ApplianceType.DEDICATED,
                pf=0.92,
                source=ApplianceSource.DEFAULT,
            )
        )


class LivingKitchen(BaseRoom):
    """Sala/Cozinha integrada para kitnets (< 35m²).

    Rules applied:
      - Lighting: Lumen Method (NBR 8995) — 300 lux (usa regra de cozinha, mais exigente)
      - General outlets: combinação de TUGs de sala + cozinha (NBR 5410)
      - Dedicated outlets: 1 for electric faucet (5500 W, 220 V)
    """

    ROOM_TYPE = "living_kitchen"

    def apply_nbr5410_rules(self) -> None:
        self._apply_lighting()
        self._apply_tugs()
        self._apply_faucet()

    def _apply_lighting(self) -> None:
        # Usa 300 lux (regra de cozinha, mais exigente que sala)
        result = lighting_calculator("kitchen", self.area, self.width, self.length)
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
        # Combina regras: mínimo 3 de 600W (cozinha) + restante 100W (sala)
        qty = max(3, math.ceil(self.perimeter / 3.5))
        for i in range(qty):
            wattage = 600 if i < 3 else 100
            self.add_appliance(
                Appliance(
                    name=f"TUG sala/cozinha {i + 1}",
                    wattage=wattage,
                    type=ApplianceType.GENERAL,
                )
            )

    def _apply_faucet(self) -> None:
        self.add_appliance(
            Appliance(
                key="living_kitchen_electric_faucet",
                name="Torneira elétrica",
                wattage=5500,
                type=ApplianceType.DEDICATED,
                voltage=220,
                source=ApplianceSource.DEFAULT,
            )
        )
