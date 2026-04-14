from models.rooms import Bathroom
from services.drawing.engine import DXFGenerator, Opening

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")



def run_powertrace_flow():
    my_bathroom = Bathroom(name="Banheiro Principal", width=3.0, length=4.0)
    my_bathroom.apply_nbr5410_rules()
    # ── Detalhes do cômodo ──────────────────────────────────────────
    print("--- Detalhes do Cômodo ---")
    print(my_bathroom)
    for app in my_bathroom.appliances:
        print(f"  {app}")

    # ── Fluxo Room → Circuit → Dimensionamento ──────────────────────
    print("\n--- Circuitos Dimensionados (NBR 5410) ---")
    circuits = my_bathroom.build_circuits()
    for circuit in circuits:
        dim = circuit.dimension()
        print(f"  {dim}")

    # ── Geração do DXF ──────────────────────────────────────────────
    window_width = 1.2
    openings = [
        Opening(wall='S', offset=0.5, width=0.8, kind='door',   swing='right'),
        Opening(wall='N', offset=(my_bathroom.width - window_width) / 2,
                width=window_width, kind='window'),
    ]

    generator = DXFGenerator()
    generator.draw_room_structure(my_bathroom, openings=openings)
    generator.draw_lighting(my_bathroom)
    generator.draw_appliances(my_bathroom, openings=openings)

    generator.save("bathroom_test.dxf")


if __name__ == "__main__":
    run_powertrace_flow()