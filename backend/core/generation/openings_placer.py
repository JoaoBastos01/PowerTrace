"""Módulo de Posicionamento Lógico de Aberturas (Portas e Janelas)."""

from typing import Dict, List
from models.floor_plan import FloorPlan
from core.drawing.openings import Opening
from core.generation.adjacency import AdjacencyGraph


class OpeningsPlacer:
    """Distribui portas e janelas com base no grafo de intersecções."""

    @staticmethod
    def _get_edge_cost(r1: str, r2: str) -> int:
        """Determina o custo arquitetônico de conectar dois cômodos."""
        def base(name):
            if name.startswith('bedroom'): return 'bedroom'
            if name.startswith('bathroom'): return 'bathroom'
            return name
        
        pair = frozenset([base(r1), base(r2)])
        costs = {
            frozenset(['corridor', 'bedroom']): 1,
            frozenset(['corridor', 'bathroom']): 1,
            frozenset(['corridor', 'living']): 1,
            frozenset(['living', 'kitchen']): 1,
            frozenset(['living_kitchen', 'bedroom']): 1,
            frozenset(['living_kitchen', 'bathroom']): 1,
            frozenset(['bedroom', 'bathroom']): 2,   # Suite
            frozenset(['living', 'bedroom']): 5,     # Acesso direto pela sala
            frozenset(['kitchen', 'corridor']): 10,  
            frozenset(['living', 'bathroom']): 20,
            frozenset(['kitchen', 'bedroom']): 50,
            frozenset(['bedroom', 'bedroom']): 50,   # Quarto "passa-prato"
            frozenset(['kitchen', 'bathroom']): 100, # Péssimo
            frozenset(['bathroom', 'bathroom']): 100,
            
            # Garage logic
            frozenset(['garage', 'living']): 1,
            frozenset(['garage', 'kitchen']): 5,
            frozenset(['garage', 'corridor']): 10,
            frozenset(['garage', 'bedroom']): 200,   # Never
            frozenset(['garage', 'bathroom']): 200,  # Never
        }
        return costs.get(pair, 200)

    @staticmethod
    def generate_openings(plan: FloorPlan, graph: AdjacencyGraph) -> Dict[str, List[Opening]]:
        """Gera o dicionário injetável de Openings para o DXFGenerator."""
        openings_dict: Dict[str, List[Opening]] = {rspec.room_type: [] for rspec in plan.rooms}
        placed_doors = set()
        
        # Build MST (Prim's algorithm) to guarantee access with minimum architectural cost
        root_room = 'living' if any(r.room_type == 'living' for r in plan.rooms) else 'living_kitchen'
        if not any(r.room_type == root_room for r in plan.rooms):
            root_room = plan.rooms[0].room_type

        visited = {root_room}
        spanning_edges = set()
        import heapq
        
        edges_pq = []
        for neighbor in graph.edges[root_room]:
            heapq.heappush(edges_pq, (OpeningsPlacer._get_edge_cost(root_room, neighbor), root_room, neighbor))
            
        while edges_pq:
            cost, u, v = heapq.heappop(edges_pq)
            if v not in visited:
                visited.add(v)
                spanning_edges.add(tuple(sorted([u, v])))
                
                # Prevent bathrooms and garages from acting as corridors/pass-throughs
                if not v.startswith('bathroom') and not v.startswith('garage'):
                    for neighbor in graph.edges[v]:
                        if neighbor not in visited:
                            heapq.heappush(edges_pq, (OpeningsPlacer._get_edge_cost(v, neighbor), v, neighbor))

        def get_rank(name):
            if name.startswith('living'): return 0
            if name.startswith('corridor'): return 1
            if name.startswith('kitchen'): return 2
            if name.startswith('bedroom'): return 3
            if name.startswith('bathroom'): return 4
            if name.startswith('garage'): return 5
            return 10

        for edge_id in spanning_edges:
            name_a, name_b = edge_id
            # r2 gets the 'door' symbol, so it swings into r2.
            # We want the door to swing into the higher ranked room.
            if get_rank(name_a) > get_rank(name_b):
                r2 = graph.rooms[name_a]
                r1 = graph.rooms[name_b]
            else:
                r2 = graph.rooms[name_b]
                r1 = graph.rooms[name_a]
                
            door_w = 0.8

            if abs((r1.x + r1.width) - r2.x) < 0.05:
                y_start = max(r1.y, r2.y)
                y_end = min(r1.y + r1.length, r2.y + r2.length)
                overlap = y_end - y_start
                if overlap < door_w: continue
                abs_y = y_start + (overlap - door_w) / 2.0
                off_r1 = abs_y - r1.y
                off_r2 = (r2.y + r2.length) - (abs_y + door_w)
                openings_dict[r1.room_type].append(Opening(wall='E', offset=off_r1, width=door_w, kind='gap', swing='right'))
                openings_dict[r2.room_type].append(Opening(wall='W', offset=off_r2, width=door_w, kind='door', swing='left'))
                continue

            if abs((r2.x + r2.width) - r1.x) < 0.05:
                y_start = max(r1.y, r2.y)
                y_end = min(r1.y + r1.length, r2.y + r2.length)
                overlap = y_end - y_start
                if overlap < door_w: continue
                abs_y = y_start + (overlap - door_w) / 2.0
                off_r2 = abs_y - r2.y
                off_r1 = (r1.y + r1.length) - (abs_y + door_w)
                openings_dict[r2.room_type].append(Opening(wall='E', offset=off_r2, width=door_w, kind='gap', swing='right'))
                openings_dict[r1.room_type].append(Opening(wall='W', offset=off_r1, width=door_w, kind='door', swing='left'))
                continue

            if abs((r1.y + r1.length) - r2.y) < 0.05:
                x_start = max(r1.x, r2.x)
                x_end = min(r1.x + r1.width, r2.x + r2.width)
                overlap = x_end - x_start
                if overlap < door_w: continue
                abs_x = x_start + (overlap - door_w) / 2.0
                off_r2 = abs_x - r2.x
                off_r1 = (r1.x + r1.width) - (abs_x + door_w)
                openings_dict[r1.room_type].append(Opening(wall='N', offset=off_r1, width=door_w, kind='gap', swing='right'))
                openings_dict[r2.room_type].append(Opening(wall='S', offset=off_r2, width=door_w, kind='door', swing='left'))
                continue

            if abs((r2.y + r2.length) - r1.y) < 0.05:
                x_start = max(r1.x, r2.x)
                x_end = min(r1.x + r1.width, r2.x + r2.width)
                overlap = x_end - x_start
                if overlap < door_w: continue
                abs_x = x_start + (overlap - door_w) / 2.0
                off_r1 = abs_x - r1.x
                off_r2 = (r2.x + r2.width) - (abs_x + door_w)
                openings_dict[r1.room_type].append(Opening(wall='S', offset=off_r1, width=door_w, kind='gap', swing='right'))
                openings_dict[r2.room_type].append(Opening(wall='N', offset=off_r2, width=door_w, kind='door', swing='left'))
                continue

        has_main_door = False
        for rspec in plan.rooms:
            if not rspec.exterior_walls:
                continue
            best_walls = sorted(list(rspec.exterior_walls),
                                key=lambda e: rspec.width if e in ['S', 'N'] else rspec.length,
                                reverse=True)
            main_ext = best_walls[0]
            wall_length = rspec.width if main_ext in ['S', 'N'] else rspec.length
            boneca = 0.20
            if not has_main_door and rspec.room_type == "living":
                has_main_door = True
                main_w = 0.9
                openings_dict[rspec.room_type].append(Opening(wall=main_ext, offset=boneca, width=main_w, kind='door', swing='right'))
                win_w = 1.2
                win_off = (wall_length / 2) - (win_w / 2)
                if win_off < (boneca + main_w + 0.3):
                    win_off = wall_length - win_w - 0.2
                if win_off > 0 and (win_off + win_w) < wall_length:
                    openings_dict[rspec.room_type].append(Opening(wall=main_ext, offset=win_off, width=win_w, kind='window'))
            elif rspec.room_type == 'garage':
                door_w = 2.5
                if wall_length >= door_w + 0.4:
                    door_off = (wall_length / 2) - (door_w / 2)
                    openings_dict[rspec.room_type].append(Opening(wall=main_ext, offset=door_off, width=door_w, kind='garage_door', swing='left'))
            else:
                win_w = 1.2
                if rspec.room_type.startswith("bathroom"):
                    win_w = 0.60
                
                # Minimum margin required (0.15m wall + 0.05m inner boneca)
                min_margin = 0.20
                if wall_length < win_w + 2 * min_margin:
                    win_w = wall_length - 2 * min_margin
                
                if win_w >= 0.40:  # Minimum acceptable window size
                    win_off = (wall_length / 2) - (win_w / 2)
                    openings_dict[rspec.room_type].append(Opening(wall=main_ext, offset=win_off, width=win_w, kind='window'))

        return openings_dict
