import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.generation.generator import FloorPlanGenerator
from services.drawing.engine import DXFGenerator
from services.generation.openings_placer import OpeningsPlacer
from models.rooms import Kitchen, Bathroom, Bedroom, Living, Corridor, Garage

CLASS_MAP = {
    "kitchen": Kitchen,
    "bathroom_1": Bathroom,
    "bathroom_2": Bathroom,
    "bedroom_1": Bedroom,
    "bedroom_2": Bedroom,
    "bedroom_3": Bedroom,
    "living": Living,
    "corridor": Corridor,
    "garage": Garage
}

def generate_and_draw():
    print("--- 1. Generating Procedural Floor Plan ---")
    gen = FloorPlanGenerator(master_seed=234234, width=8.0, length=10.0)
    try:
        plan, graph = gen.generate(max_attempts=100)
    except Exception as e:
        print(f"Erro na geração: {e}")
        return
        
    print(f"Success! Seed: {plan.seed} | Area: {plan.total_area}m²")
    
    print("\n--- 2. Calculando Portas e Janelas ---")
    openings_dict = OpeningsPlacer.generate_openings(plan, graph)
    
    print("\n--- 3. Building DXF File ---")
    dxf_gen = DXFGenerator()
    
    count = 0
    for rspec in plan.rooms:
        print(f"  -> Processando {rspec.room_type.capitalize()} na Origem: ({rspec.x:.1f}, {rspec.y:.1f})")
        
        RoomClass = CLASS_MAP.get(rspec.room_type, Living)
        
        room_instance = RoomClass(
            name=f"{rspec.room_type.replace('_', ' ').title()}",
            width=rspec.width,
            length=rspec.length,
            origin=(rspec.x, rspec.y)
        )
        # Importante: O DXF agora lê exterior_walls do objeto da sala para retrair as faces compartilhadas!
        room_instance.exterior_walls = rspec.exterior_walls
        room_instance.apply_nbr5410_rules()
        
        ops = openings_dict.get(rspec.room_type, [])
        for op in ops:
             print(f"       + {op.kind.title()} na parede {op.wall} (w={op.width}m)")
             
        # Desenhando com o recuo inteligente das paredes
        dxf_gen.draw_room_structure(room_instance, openings=ops)
        dxf_gen.draw_lighting(room_instance)
        count += len(room_instance.appliances)
        
        # O draw_appliances tem lógicas q fogem das aberturas
        dxf_gen.draw_appliances(room_instance, openings=ops)
        
    filename = "procedural_house.dxf"
    dxf_gen.save(filename)
    print("\nDXF Salvo! O arquivo gerou a planta procedimental perfeita com portas e paredes em linha dupla.")

if __name__ == "__main__":
    generate_and_draw()
