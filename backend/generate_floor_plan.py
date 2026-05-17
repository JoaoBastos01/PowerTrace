"""Script de integração para gerar uma planta baixa completa.

Este script conecta o gerador (FloorPlanGenerator) com o posicionador
de aberturas (OpeningsPlacer) e a engine de desenho (DXFGenerator).
"""

import sys
import io
import argparse

from services.generation.generator import FloorPlanGenerator
from services.generation.openings_placer import OpeningsPlacer
from services.drawing.engine import DXFGenerator
from models.rooms import Kitchen, Bedroom, Bathroom, Living, Corridor, Garage, LivingKitchen

# Garante que prints não quebrem no Windows com caracteres especiais
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def room_spec_to_base_room(room_spec):
    """Converte um RoomSpec gerado pelo BSP em uma instância concreta de BaseRoom."""
    # Mapeamento do room_type string para a classe correspondente
    room_classes = {
        "kitchen": Kitchen,
        "bedroom_1": Bedroom,
        "bedroom_2": Bedroom,
        "bedroom_3": Bedroom,
        "bathroom_1": Bathroom,
        "bathroom_2": Bathroom,
        "living": Living,
        "corridor": Corridor,
        "garage": Garage,
        "living_kitchen": LivingKitchen,
    }

    room_class = room_classes.get(room_spec.room_type)
    if not room_class:
        raise ValueError(f"Tipo de cômodo desconhecido: {room_spec.room_type}")

    # Instancia o cômodo com os dados geométricos do RoomSpec
    room_obj = room_class(
        name=room_spec.room_type.replace("_", " ").title(),
        width=room_spec.width,
        length=room_spec.length,
        origin=room_spec.origin
    )
    # Copia os exterior_walls pro objeto pro DXFGenerator saber desenhar o muro grosso
    room_obj.exterior_walls = room_spec.exterior_walls
    return room_obj


def generate_full_plan(seed: int, width: float, length: float, output_file: str):
    """Gera a planta completa, aplica as regras elétricas e salva o DXF."""
    print(f"--- Gerando planta: {width}m x {length}m (Seed: {seed}) ---")

    # 1. Geração da Topologia e Layout
    try:
        plan, graph, program = FloorPlanGenerator(seed, width, length).generate()
    except ValueError as e:
        print(f"Erro na geração: {e}")
        return

    print(f"Categoria da casa: {program.category}")
    print(f"Cômodos gerados: {len(plan.rooms)}")

    # 2. Posicionamento de Aberturas (Portas e Janelas)
    openings_dict = OpeningsPlacer.generate_openings(plan, graph)

    # 3. Desenho do DXF
    generator = DXFGenerator()

    for room_spec in plan.rooms:
        # Converter RoomSpec (geometria) para BaseRoom (elétrica)
        room_obj = room_spec_to_base_room(room_spec)
        
        # Aplicar regras de carga (NBR 5410/8995)
        room_obj.apply_nbr5410_rules()
        
        # Desenhar no DXF
        room_openings = openings_dict.get(room_spec.room_type, [])
        generator.draw_room_structure(room_obj, openings=room_openings)
        generator.draw_lighting(room_obj)
        generator.draw_appliances(room_obj, openings=room_openings)

        # Print informações do cômodo (opcional, para debug/log)
        print(f"  - {room_obj.name}: {room_obj.area:.1f}m² ({room_obj.get_total_wattage()}W)")

    # 4. Salvar arquivo
    generator.save(output_file)
    print(f"\nPlanta salva com sucesso em: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera uma planta baixa elétrica completa em DXF.")
    parser.add_argument("--seed", type=int, default=42, help="Seed para a geração procedural.")
    parser.add_argument("--width", type=float, default=6.0, help="Largura do terreno/casa (m).")
    parser.add_argument("--length", type=float, default=10.0, help="Comprimento do terreno/casa (m).")
    parser.add_argument("--output", type=str, default="full_plan.dxf", help="Nome do arquivo de saída.")

    args = parser.parse_args()
    generate_full_plan(args.seed, args.width, args.length, args.output)
