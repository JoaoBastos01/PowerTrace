from backend.models.rooms import Kitchen
from backend.services.drawing.engine import DXFGenerator

def run_powertrace_flow():
    my_kitchen = Kitchen(name="Cozinha Principal", width=4.0, length=3.0)
    
    my_kitchen.apply_nbr5410_rules()
    
    print(f"--- Room Details ---")
    print(my_kitchen) 
    for app in my_kitchen.appliances:
        print(f"  {app}")
    
    generator = DXFGenerator()
    generator.draw_room(my_kitchen)
    generator.draw_appliances(my_kitchen)
    generator.draw_door(my_kitchen.origin[0] + 0.2, my_kitchen.origin[1])
    
    generator.save("kitchen_test.dxf")

if __name__ == "__main__":
    run_powertrace_flow()