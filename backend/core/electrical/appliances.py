from enum import Enum


class ApplianceType(Enum):
    GENERAL = "general"
    DEDICATED = "dedicated"
    LIGHTING = "lighting"


class ApplianceSource(str, Enum):
    DEFAULT = "default"
    CUSTOM = "custom"


class Appliance:
    def __init__(
        self,
        name: str,
        wattage: int,
        type: ApplianceType = ApplianceType.GENERAL,
        voltage: int = 127,
        pf: float = 1.0,
        key: str | None = None,
        source: ApplianceSource = ApplianceSource.DEFAULT,
    ):
        self.name = name
        self.wattage = wattage
        self.type = type
        self.voltage = voltage
        self.pf = pf
        self.key = key
        self.source = source

    def __repr__(self):
        return f"<{self.type.value}: {self.name} ({self.wattage}W)>"
