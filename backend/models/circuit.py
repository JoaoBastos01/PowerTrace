from standards.nbr5410 import ElectricalStandards

class Circuit:
    def __init__(self, circuit_id, voltage=127, pf=0.92):
        self.circuit_id = circuit_id
        self.voltage = voltage
        self.pf = pf
        self.load_points = []
        self.description = ""
        
    def add_load_point(self, load_point):
        self.load_points.append(load_point)
        
    @property
    def total_wattage(self):
        return sum(load_point.wattage for load_point in self.load_points)
    
    def calculate_current(self):
        base_current = self.total_wattage / (self.voltage * self.pf)
        return base_current * 1.10
    
    def dimension_protection(self):
        current = self.calculate_current()
        breaker = next((b for b in ElectricalStandards.COMERCIAL_CIRCUIT_BREAKERS if b >= current), ElectricalStandards.COMERCIAL_CIRCUIT_BREAKERS[-1])
        
        for gauge, max_amp, res in ElectricalStandards.WIRE_GAUGE_TABLE:
            if max_amp >= breaker:
                return {
                    "current": f"{current:.2f}A",
                    "breaker": f"{breaker}A",
                    "gauge": f"{gauge}mm²",
                    "max_amp": f"{max_amp}A",
                    "resistance": f"{res}Ω/km"
                }
        raise ValueError(f"Circuit '{self.circuit_id}': A carga de {self.total_wattage}W excede a capacidade máxima da tabela da NBR 5410")