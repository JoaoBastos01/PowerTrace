from abc import ABC, abstractmethod

class BaseRoom(ABC):
    def __init__(self, name, width, length, voltage=127, origin=(0, 0)):
        self.name = name
        self.width = width
        self.length = length
        self.voltage = voltage
        self.origin = origin
        self.appliances = []
        
    @property
    def area(self):
        return self.width * self.length
    
    @property
    def perimeter(self):
        return 2 * (self.width + self.length)
    
    @abstractmethod
    def apply_nbr5410_rules(self):
        """Aplica as regras específicas para o tipo de ambiente, como número mínimo de pontos de carga, distribuição de circuitos, etc."""
        pass
    
    def add_appliance(self, appliance):
        self.appliances.append(appliance)
        
    def get_total_wattage(self):
        return sum(appliance.wattage for appliance in self.appliances)
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, area={self.area}m², voltage={self.voltage}V, appliances={len(self.appliances)})"