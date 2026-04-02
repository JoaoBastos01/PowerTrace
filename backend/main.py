from models.rooms import Kitchen
from services.drawing.engine import DXFGenerator, Opening


def run_powertrace_flow():
    my_kitchen = Kitchen(name="Cozinha Principal", width=7.0, length=7.0)
    my_kitchen.apply_nbr5410_rules()

    print("--- Detalhes do Cômodo ---")
    print(my_kitchen)
    for app in my_kitchen.appliances:
        print(f"  {app}")

    # Janela na parede norte, centralizada: offset = (largura_parede - largura_janela) / 2
    window_width = 1.2
    openings = [
        Opening(wall='S', offset=0.5, width=0.8, kind='door',   swing='right'),
        Opening(wall='N', offset=(my_kitchen.width - window_width) / 2,
                width=window_width, kind='window'),
    ]

    generator = DXFGenerator()
    generator.draw_room_structure(my_kitchen, openings=openings)
    generator.draw_lighting(my_kitchen)
    generator.draw_appliances(my_kitchen)
    generator.save("kitchen_test.dxf")


if __name__ == "__main__":
    run_powertrace_flow()