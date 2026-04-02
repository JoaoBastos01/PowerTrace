from enum import Enum

class ApplianceType(Enum):
    GENERAL = "general"
    DEDICATED = "dedicated"
    LIGHTING = "lighting"

class Appliance:
    def __init__(self, name: str, wattage: int, type: ApplianceType = ApplianceType.GENERAL, voltage: int = 127):
        self.name = name
        self.wattage = wattage
        self.type = type
        self.voltage = voltage
        
    def __repr__(self):
        return f"<{self.type.value}: {self.name} ({self.wattage}W)>"