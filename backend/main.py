from backend.models.rooms import Kitchen
from backend.services.drawing.engine import DXFGenerator, Opening

def run_powertrace_flow():
    my_kitchen = Kitchen(name="Cozinha Principal", width=4.0, length=3.0)
    my_kitchen.apply_nbr5410_rules()

    print("--- Detalhes do Cômodo ---")
    print(my_kitchen)
    for app in my_kitchen.appliances:
        print(f"  {app}")

    # Define as aberturas: uma porta na parede sul e uma janela na parede norte
    openings = [
        Opening(wall='S', offset=0.5, width=0.8, kind='door',   swing='right'),
        Opening(wall='N', offset=1.0, width=1.2, kind='window'),
    ]

    generator = DXFGenerator()
    generator.draw_room_structure(my_kitchen, openings=openings)
    generator.draw_appliances(my_kitchen)
    generator.save("kitchen_test.dxf")

if __name__ == "__main__":
    run_powertrace_flow()