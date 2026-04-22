"""Base model to all the PoweTrace's rooms."""

from abc import ABC, abstractmethod
from typing import List

from .appliances import Appliance, ApplianceType

_VALID_ROOM_TYPES = {"kitchen", "bedroom", "living", "bathroom", "corridor", "garage"}


class BaseRoom(ABC):
    """Generic room with dimensions, loads and NBR 5410 circuit generation."""

    ROOM_TYPE: str  # required in every concrete subclass

    def __init_subclass__(cls, **kwargs):
        """Ensures that every concrete subclass declares a valid ROOM_TYPE."""
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "__abstractmethods__", None):  # is concrete
            if "ROOM_TYPE" not in cls.__dict__:
                raise TypeError(
                    f"'{cls.__name__}' deve declarar ROOM_TYPE. "
                    f"Valores válidos: {sorted(_VALID_ROOM_TYPES)}"
                )
            if cls.__dict__["ROOM_TYPE"] not in _VALID_ROOM_TYPES:
                raise ValueError(
                    f"'{cls.__name__}.ROOM_TYPE = {cls.__dict__['ROOM_TYPE']!r}' inválido. "
                    f"Valores válidos: {sorted(_VALID_ROOM_TYPES)}"
                )

    def __init__(
        self,
        name: str,
        width: float,
        length: float,
        voltage: int = 127,
        origin: tuple = (0, 0),
    ):
        self.name = name
        self.width = width
        self.length = length
        self.voltage = voltage
        self.origin = origin
        self.appliances: List[Appliance] = []

    # ------------------------------------------------------------------
    # Geometric properties
    # ------------------------------------------------------------------

    @property
    def area(self) -> float:
        return self.width * self.length

    @property
    def perimeter(self) -> float:
        return 2 * (self.width + self.length)

    # ------------------------------------------------------------------
    # Load management
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
        """Applies NBR 5410 rules specific to this room type.

        Each subclass must fill `self.appliances` with the load points
        required by the standard (TUGs, lighting, dedicated).
        """

    def build_circuits(self) -> list:
        """Groups appliances into circuits according to NBR 5410.

        Grouping rules:
          - LIGHTING   → 1 lighting circuit per room
          - GENERAL    → 1 general TUG circuit per room
          - DEDICATED  → 1 dedicated circuit per dedicated load

        Returns:
            List of already populated Circuits, ready for sizing.
        """
        from .circuit import Circuit  # local import to avoid cycle

        circuits = []

        # ── Lighting ────────────────────────────────────────────────
        lighting = [a for a in self.appliances if a.type == ApplianceType.LIGHTING]
        if lighting:
            c = Circuit(f"{self.name}_LUZ", voltage=self.voltage)
            for a in lighting:
                c.add_load_point(a)
            circuits.append(c)

        # ── General circuits ─────────────────────────────────────────
        general = [a for a in self.appliances if a.type == ApplianceType.GENERAL]
        if general:
            c = Circuit(f"{self.name}_TUG", voltage=self.voltage)
            for a in general:
                c.add_load_point(a)
            circuits.append(c)

        # ── Dedicated circuits (one per load) ────────────────────────
        dedicated = [a for a in self.appliances if a.type == ApplianceType.DEDICATED]
        for a in dedicated:
            c = Circuit(
                f"{self.name}_{a.name.upper().replace(' ', '_')}",
                voltage=a.voltage,
                pf=a.pf,
            )
            c.add_load_point(a)
            circuits.append(c)

        return circuits

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"name={self.name}, "
            f"area={self.area}m², "
            f"voltage={self.voltage}V, "
            f"appliances={len(self.appliances)})"
        )
