import sys
from app.config import settings
from core.generation.generator import FloorPlanGenerator

def debug():
    plan, graph, program = FloorPlanGenerator(42, 8.0, 12.0).generate(50)
    for room in plan.rooms:
        print(f"{room.room_type}: x={room.x}, y={room.y}, w={room.width}, l={room.length}")
    for room, adjs in graph.edges.items():
        print(f"Edges of {room}: {adjs}")

if __name__ == "__main__":
    debug()
