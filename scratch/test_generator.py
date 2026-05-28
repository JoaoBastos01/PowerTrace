import os
import sys
import logging
logging.basicConfig(level=logging.DEBUG)
sys.path.insert(0, os.path.abspath(os.path.join('.', 'backend')))

from services.generation.generator import FloorPlanGenerator

try:
    generator = FloorPlanGenerator(master_seed=42, width=10.0, length=15.0)
    plan, graph, program = generator.generate()
    print("Generation successful!")
    print(f"Rooms generated: {len(plan.rooms)}")
    for r in plan.rooms:
        print(f" - {r.room_type}: {r.width}x{r.length}")
except Exception as e:
    import traceback
    traceback.print_exc()
