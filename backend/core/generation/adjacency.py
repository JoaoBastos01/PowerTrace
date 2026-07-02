"""Architectural Pathfinding and Adjacency Validation Module."""

from typing import List, Dict, Set
from models.floor_plan import RoomSpec
from .bsp import BSPNode


class AdjacencyGraph:
    """Monta o grafo de conexões físicas entre cômodos e valida regras de arquitetura."""

    DOOR_MIN_SPACE = 1.2

    def __init__(self, nodes: List[BSPNode]):
        self.rooms: Dict[str, RoomSpec] = {}
        for node in nodes:
            name = node.room_type
            self.rooms[name] = RoomSpec(
                room_type=name,
                x=node.x,
                y=node.y,
                width=node.width,
                length=node.length,
                exterior_walls=frozenset(node.exterior_walls)
            )
        self.edges: Dict[str, Set[str]] = {name: set() for name in self.rooms}
        self._build_edges()

    def _build_edges(self):
        room_names = sorted(self.rooms.keys())
        for i in range(len(room_names)):
            for j in range(i + 1, len(room_names)):
                r1 = self.rooms[room_names[i]]
                r2 = self.rooms[room_names[j]]
                if abs((r1.x + r1.width) - r2.x) < 0.05 or abs((r2.x + r2.width) - r1.x) < 0.05:
                    overlap_y = min(r1.y + r1.length, r2.y + r2.length) - max(r1.y, r2.y)
                    if overlap_y >= self.DOOR_MIN_SPACE:
                        self.edges[r1.room_type].add(r2.room_type)
                        self.edges[r2.room_type].add(r1.room_type)
                if abs((r1.y + r1.length) - r2.y) < 0.05 or abs((r2.y + r2.length) - r1.y) < 0.05:
                    overlap_x = min(r1.x + r1.width, r2.x + r2.width) - max(r1.x, r2.x)
                    if overlap_x >= self.DOOR_MIN_SPACE:
                        self.edges[r1.room_type].add(r2.room_type)
                        self.edges[r2.room_type].add(r1.room_type)

    def validate_architecture(self) -> bool:
        if not self._is_connected():
            return False
        for room in sorted(self.edges.keys()):
            adjacencies = self.edges[room]
            if room == "bathroom_social":
                # Social bathroom must connect to social hubs only
                allowed_hubs = {"living", "living_kitchen", "corridor"}
                if not any(hub in adjacencies for hub in allowed_hubs):
                    return False
            elif room.startswith("bathroom"):
                # Private bathrooms: connect to corridor or bedrooms
                allowed_hubs = {"living", "living_kitchen", "corridor"} | {k for k in self.edges if k.startswith("bedroom")}
                if not any(hub in adjacencies for hub in allowed_hubs):
                    return False
            if room.startswith("bedroom"):
                allowed_hubs = {"living", "living_kitchen", "corridor"}
                if not any(hub in adjacencies for hub in allowed_hubs):
                    return False
            if room.startswith("kitchen") and not room.startswith("living_kitchen"):
                allowed_hubs = {"living", "corridor"}
                if not any(hub in adjacencies for hub in allowed_hubs):
                    return False
            if room.startswith("garage"):
                allowed_hubs = {"living", "corridor", "kitchen"}
                if not any(hub in adjacencies for hub in allowed_hubs):
                    return False
        return True

    def _is_connected(self) -> bool:
        if not self.rooms: return True
        start = min(self.rooms.keys())
        visited = set()
        queue = [start]
        while queue:
            curr = queue.pop(0)
            if curr not in visited:
                visited.add(curr)
                queue.extend(self.edges[curr] - visited)
        return len(visited) == len(self.rooms)
