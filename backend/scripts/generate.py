"""Script CLI para geração de planta baixa completa em DXF.

Uso:
    python scripts/generate.py --seed 42 --width 8.0 --length 12.0
    python scripts/generate.py --seed 7 --width 10.0 --length 15.0 --output grande.dxf
"""

import sys
import argparse
import logging

from app.config import settings
from core.generation.generator import FloorPlanGenerator
from core.generation.openings_placer import OpeningsPlacer
from core.drawing.engine import DXFGenerator
from core.electrical.room_catalog import room_spec_to_base_room

# ── Logging centralizado ────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(levelname)s:%(name)s:%(message)s",
)


def generate_full_plan(seed: int, width: float, length: float, output_file: str) -> None:
    """Gera a planta completa, aplica as regras elétricas e salva o DXF."""
    print(f"--- Gerando planta: {width}m x {length}m (Seed: {seed}) ---")

    # 1. Geração da Topologia e Layout
    try:
        plan, graph, program = FloorPlanGenerator(seed, width, length).generate(
            max_attempts=settings.max_generation_attempts
        )
    except ValueError as e:
        print(f"Erro na geração: {e}")
        sys.exit(1)

    print(f"Categoria da casa: {program.category}")
    print(f"Cômodos gerados: {len(plan.rooms)}")

    # 2. Posicionamento de Aberturas (Portas e Janelas)
    openings_dict = OpeningsPlacer.generate_openings(plan, graph)

    # 3. Desenho do DXF
    generator = DXFGenerator()

    for room_spec in plan.rooms:
        room_obj = room_spec_to_base_room(room_spec)
        room_obj.apply_nbr5410_rules()

        room_openings = openings_dict.get(room_spec.room_type, [])
        generator.draw_room_structure(room_obj, openings=room_openings)
        generator.draw_lighting(room_obj)
        generator.draw_appliances(room_obj, openings=room_openings)

        print(f"  - {room_obj.name}: {room_obj.area:.1f}m² ({room_obj.get_total_wattage()}W)")

    # 4. Salvar arquivo
    saved_path = generator.save(output_file)
    print(f"\nPlanta salva com sucesso em: {saved_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera uma planta baixa elétrica completa em DXF.")
    parser.add_argument("--seed",   type=int,   default=42,          help="Seed para a geração procedural.")
    parser.add_argument("--width",  type=float, default=6.0,         help="Largura do terreno/casa (m).")
    parser.add_argument("--length", type=float, default=10.0,        help="Comprimento do terreno/casa (m).")
    parser.add_argument("--output", type=str,   default="full_plan.dxf", help="Nome do arquivo de saída.")

    args = parser.parse_args()
    generate_full_plan(args.seed, args.width, args.length, args.output)
