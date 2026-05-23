import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.generation.generator import FloorPlanGenerator
from core.drawing.geometry import DXFGenerator
from core.electrical.standards import OpeningsPlacer
from core.electrical.standards import Kitchen, Bathroom, Bedroom, Living, Corridor, Garage, LivingKitchen

# Mapa de room_type → Classe NBR 5410
# O room_type vem do generator (ex: "bedroom_1", "bathroom_2")
# Precisamos mapear para a classe base (ex: Bedroom, Bathroom)
def get_room_class(room_type: str):
    """Retorna a classe de sala correta baseado no room_type."""
    if room_type.startswith("bedroom"):
        return Bedroom
    if room_type.startswith("bathroom"):
        return Bathroom
    if room_type == "living_kitchen":
        return LivingKitchen

    CLASS_MAP = {
        "kitchen": Kitchen,
        "living": Living,
        "corridor": Corridor,
        "garage": Garage,
    }
    return CLASS_MAP.get(room_type, Living)


def generate_and_draw():
    # ── Configuração ─────────────────────────────────────────────
    SEED = 234234
    WIDTH = 8.0
    LENGTH = 10.0

    print("=" * 60)
    print("  PowerTrace — Gerador Topology-First")
    print("=" * 60)

    # ── Fase 1 + 2: Program + Layout ─────────────────────────────
    print("\n--- Fase 1+2: Gerando Program + Layout ---")
    gen = FloorPlanGenerator(master_seed=SEED, width=WIDTH, length=LENGTH)
    try:
        plan, graph, program = gen.generate(max_attempts=100)
    except Exception as e:
        print(f"Erro na geração: {e}")
        return

    print(f"  Seed: {plan.seed} | Área: {plan.total_area}m² | Categoria: {program.category}")
    print(f"  Cômodos: {list(program.rooms.keys())}")
    print(f"  Topologia: {program.topology}")

    # ── Fase 3: Aberturas ────────────────────────────────────────
    print("\n--- Fase 3: Calculando Portas e Janelas ---")
    openings_dict = OpeningsPlacer.generate_openings(plan, graph)

    # ── Desenho DXF ──────────────────────────────────────────────
    print("\n--- Fase 4: Gerando DXF ---")
    dxf_gen = DXFGenerator()

    for rspec in plan.rooms:
        print(f"  -> {rspec.room_type.capitalize()} | Pos: ({rspec.x:.1f}, {rspec.y:.1f}) | "
              f"Dim: {rspec.width:.1f}×{rspec.length:.1f}m | "
              f"Ext: {set(rspec.exterior_walls)}")

        RoomClass = get_room_class(rspec.room_type)

        room_instance = RoomClass(
            name=f"{rspec.room_type.replace('_', ' ').title()}",
            width=rspec.width,
            length=rspec.length,
            origin=(rspec.x, rspec.y)
        )
        room_instance.exterior_walls = rspec.exterior_walls
        room_instance.apply_nbr5410_rules()

        ops = openings_dict.get(rspec.room_type, [])
        for op in ops:
            print(f"       + {op.kind.title()} na parede {op.wall} (w={op.width}m)")

        dxf_gen.draw_room_structure(room_instance, openings=ops)
        dxf_gen.draw_lighting(room_instance)
        dxf_gen.draw_appliances(room_instance, openings=ops)

    filename = "procedural_house.dxf"
    dxf_gen.save(filename)
    print(f"\n[OK] DXF salvo: {filename}")
    print("   Planta gerada com topologia respeitada!")


if __name__ == "__main__":
    generate_and_draw()
