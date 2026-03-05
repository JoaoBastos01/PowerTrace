class Appliance:
    def __init__(self, name, wattage, type="general", voltage=127):
        self.name = name
        self.wattage = wattage
        self.type = type
        self.voltage = voltage
        
    def __repr__(self):
        return f"<{self.type}: {self.name} ({self.wattage}W)>"