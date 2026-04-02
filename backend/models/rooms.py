from .base import BaseRoom
from .appliances import Appliance

class Kitchen(BaseRoom):
    def apply_nbr5410_rules(self):
        qty = int(-(-self.perimeter // 3.5))
        
        for i in range(qty):
            wattage = 600 if i < 3 else 100
            self.add_appliance(Appliance(name=f"TUG cozinha {i+1}", wattage=wattage))
        pass
    
    