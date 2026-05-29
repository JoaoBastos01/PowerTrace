"""Módulo de Posicionamento Lógico de Aberturas (Portas e Janelas)."""

import math
from typing import Dict, List, Tuple
from models.floor_plan import FloorPlan
from core.drawing.openings import Opening
from core.generation.adjacency import AdjacencyGraph


class OpeningsPlacer:
    """Distribui portas e janelas com base no grafo de intersecções."""

    DOOR_CANDIDATE_STEP = 0.20
    DOOR_CLEARANCE = 0.05

    @staticmethod
    def _get_edge_cost(r1: str, r2: str) -> int:
        """Determina o custo arquitetônico de conectar dois cômodos."""
        def base(name):
            if name.startswith('bedroom'): return 'bedroom'
            if name == 'bathroom_social': return 'bathroom_social'
            if name.startswith('bathroom'): return 'bathroom'
            return name
        
        pair = frozenset([base(r1), base(r2)])
        costs = {
            frozenset(['corridor', 'bedroom']): 1,
            frozenset(['corridor', 'bathroom']): 1,
            frozenset(['corridor', 'living']): 1,
            frozenset(['living', 'kitchen']): 1,
            frozenset(['living', 'bathroom_social']): 1,   # Social bathroom off living
            frozenset(['living_kitchen', 'bedroom']): 1,
            frozenset(['living_kitchen', 'bathroom']): 1,
            frozenset(['living_kitchen', 'bathroom_social']): 1,
            frozenset(['bedroom', 'bathroom']): 2,   # Suite
            frozenset(['living', 'bedroom']): 5,     # Acesso direto pela sala
            frozenset(['kitchen', 'corridor']): 10,  
            frozenset(['living', 'bathroom']): 20,
            frozenset(['kitchen', 'bedroom']): 50,
            frozenset(['bedroom', 'bedroom']): 50,   # Quarto "passa-prato"
            frozenset(['kitchen', 'bathroom']): 100, # Péssimo
            frozenset(['bathroom', 'bathroom']): 100,
            frozenset(['bedroom', 'bathroom_social']): 200,  # Never — social banheiro off bedroom
            frozenset(['bathroom_social', 'bathroom']): 200, # Never
            
            # Garage logic
            frozenset(['garage', 'living']): 1,
            frozenset(['garage', 'kitchen']): 5,
            frozenset(['garage', 'corridor']): 10,
            frozenset(['garage', 'bedroom']): 200,   # Never
            frozenset(['garage', 'bathroom']): 200,  # Never
            frozenset(['garage', 'bathroom_social']): 200,  # Never
        }
        return costs.get(pair, 200)

    @staticmethod
    def _wall_points(room, wall: str) -> Tuple[tuple, tuple]:
        x, y = room.x, room.y
        w, l = room.width, room.length
        return {
            'S': ((x, y), (x + w, y)),
            'E': ((x + w, y), (x + w, y + l)),
            'N': ((x + w, y + l), (x, y + l)),
            'W': ((x, y + l), (x, y)),
        }[wall]

    @staticmethod
    def _offset_from_absolute_start(room, wall: str, absolute_start: float, width: float) -> float:
        if wall == 'E':
            return absolute_start - room.y
        if wall == 'W':
            return (room.y + room.length) - (absolute_start + width)
        if wall == 'S':
            return absolute_start - room.x
        return (room.x + room.width) - (absolute_start + width)

    @staticmethod
    def _absolute_start_from_opening(room, opening: Opening) -> float:
        if opening.wall == 'E':
            return room.y + opening.offset
        if opening.wall == 'W':
            return room.y + room.length - opening.offset - opening.width
        if opening.wall == 'S':
            return room.x + opening.offset
        return room.x + room.width - opening.offset - opening.width

    @staticmethod
    def _offset_bounds_from_absolute_span(
        room,
        wall: str,
        absolute_min: float,
        absolute_max: float,
        width: float,
    ) -> Tuple[float, float]:
        first = OpeningsPlacer._offset_from_absolute_start(room, wall, absolute_min, width)
        last = OpeningsPlacer._offset_from_absolute_start(room, wall, absolute_max, width)
        return min(first, last), max(first, last)

    @staticmethod
    def _offset_candidates(preferred: float, minimum: float, maximum: float) -> List[float]:
        if maximum < minimum:
            return []

        preferred = max(minimum, min(preferred, maximum))
        candidates = []
        seen = set()

        def add(value: float) -> None:
            value = max(minimum, min(value, maximum))
            key = round(value, 8)
            if key not in seen:
                seen.add(key)
                candidates.append(key)

        add(preferred)
        span = max(abs(preferred - minimum), abs(maximum - preferred))
        steps = int(math.ceil(span / OpeningsPlacer.DOOR_CANDIDATE_STEP))
        for step in range(1, steps + 1):
            delta = OpeningsPlacer.DOOR_CANDIDATE_STEP * step
            add(preferred - delta)
            add(preferred + delta)
        add(minimum)
        add(maximum)
        return candidates

    @staticmethod
    def _swing_candidates(preferred: str) -> List[str]:
        opposite = 'left' if preferred == 'right' else 'right'
        return [preferred, opposite]

    @staticmethod
    def _door_footprint(room, opening: Opening) -> Tuple[float, float, float, float]:
        wall_start, wall_end = OpeningsPlacer._wall_points(room, opening.wall)
        dx = wall_end[0] - wall_start[0]
        dy = wall_end[1] - wall_start[1]
        length = math.hypot(dx, dy)
        if length == 0:
            return (wall_start[0], wall_start[1], wall_start[0], wall_start[1])

        ux, uy = dx / length, dy / length
        in_x, in_y = -uy, ux
        closed_start = (
            wall_start[0] + ux * opening.offset,
            wall_start[1] + uy * opening.offset,
        )
        closed_end = (
            wall_start[0] + ux * (opening.offset + opening.width),
            wall_start[1] + uy * (opening.offset + opening.width),
        )
        hinge = closed_start if opening.swing == 'right' else closed_end
        open_end = (
            hinge[0] + in_x * opening.width,
            hinge[1] + in_y * opening.width,
        )

        xs = [closed_start[0], closed_end[0], hinge[0], open_end[0]]
        ys = [closed_start[1], closed_end[1], hinge[1], open_end[1]]
        clearance = OpeningsPlacer.DOOR_CLEARANCE
        return (
            min(xs) - clearance,
            min(ys) - clearance,
            max(xs) + clearance,
            max(ys) + clearance,
        )

    @staticmethod
    def _overlap_area(
        first: Tuple[float, float, float, float],
        second: Tuple[float, float, float, float],
    ) -> float:
        overlap_w = min(first[2], second[2]) - max(first[0], second[0])
        overlap_h = min(first[3], second[3]) - max(first[1], second[1])
        if overlap_w <= 0 or overlap_h <= 0:
            return 0.0
        return round(overlap_w * overlap_h, 10)

    @staticmethod
    def _resolve_door_opening(
        room,
        wall: str,
        preferred_offset: float,
        width: float,
        preferred_swing: str,
        occupied_footprints: List[Tuple[float, float, float, float]],
        minimum_offset: float,
        maximum_offset: float,
    ) -> Tuple[Opening, Tuple[float, float, float, float]]:
        candidates = OpeningsPlacer._offset_candidates(
            preferred_offset,
            minimum_offset,
            maximum_offset,
        )
        if not candidates:
            fallback = Opening(wall=wall, offset=preferred_offset, width=width, kind='door', swing=preferred_swing)
            return fallback, OpeningsPlacer._door_footprint(room, fallback)

        best_score = None
        best_opening = None
        best_footprint = None
        for offset_index, offset in enumerate(candidates):
            for swing_index, swing in enumerate(OpeningsPlacer._swing_candidates(preferred_swing)):
                opening = Opening(wall=wall, offset=offset, width=width, kind='door', swing=swing)
                footprint = OpeningsPlacer._door_footprint(room, opening)
                overlap_areas = [
                    OpeningsPlacer._overlap_area(footprint, occupied)
                    for occupied in occupied_footprints
                ]
                collision_count = sum(1 for area in overlap_areas if area > 0)
                total_overlap = round(sum(overlap_areas), 10)
                score = (
                    collision_count,
                    total_overlap,
                    swing_index,
                    round(abs(offset - preferred_offset), 8),
                    offset_index,
                    round(offset, 8),
                )
                if best_score is None or score < best_score:
                    best_score = score
                    best_opening = opening
                    best_footprint = footprint

        return best_opening, best_footprint

    @staticmethod
    def _add_internal_door_pair(
        openings_dict: Dict[str, List[Opening]],
        occupied_doors: Dict[str, List[Tuple[float, float, float, float]]],
        gap_room,
        gap_wall: str,
        door_room,
        door_wall: str,
        absolute_start: float,
        overlap_start: float,
        overlap_end: float,
        width: float,
        preferred_swing: str,
    ) -> None:
        preferred_offset = OpeningsPlacer._offset_from_absolute_start(
            door_room,
            door_wall,
            absolute_start,
            width,
        )
        min_offset, max_offset = OpeningsPlacer._offset_bounds_from_absolute_span(
            door_room,
            door_wall,
            overlap_start,
            overlap_end - width,
            width,
        )
        door_opening, footprint = OpeningsPlacer._resolve_door_opening(
            door_room,
            door_wall,
            preferred_offset,
            width,
            preferred_swing,
            occupied_doors[door_room.room_type],
            min_offset,
            max_offset,
        )
        resolved_start = OpeningsPlacer._absolute_start_from_opening(door_room, door_opening)
        gap_offset = OpeningsPlacer._offset_from_absolute_start(
            gap_room,
            gap_wall,
            resolved_start,
            width,
        )

        openings_dict[gap_room.room_type].append(
            Opening(wall=gap_wall, offset=gap_offset, width=width, kind='gap', swing='right')
        )
        openings_dict[door_room.room_type].append(door_opening)
        occupied_doors[door_room.room_type].append(footprint)

    @staticmethod
    def generate_openings(plan: FloorPlan, graph: AdjacencyGraph) -> Dict[str, List[Opening]]:
        """Gera o dicionário injetável de Openings para o DXFGenerator."""
        openings_dict: Dict[str, List[Opening]] = {rspec.room_type: [] for rspec in plan.rooms}
        occupied_doors: Dict[str, List[Tuple[float, float, float, float]]] = {
            rspec.room_type: [] for rspec in plan.rooms
        }
        # Build MST (Prim's algorithm) to guarantee access with minimum architectural cost
        root_room = 'living' if any(r.room_type == 'living' for r in plan.rooms) else 'living_kitchen'
        if not any(r.room_type == root_room for r in plan.rooms):
            root_room = plan.rooms[0].room_type

        visited = {root_room}
        spanning_edges = set()
        import heapq
        
        edges_pq = []
        for neighbor in sorted(graph.edges[root_room]):
            heapq.heappush(edges_pq, (OpeningsPlacer._get_edge_cost(root_room, neighbor), root_room, neighbor))
            
        while edges_pq:
            cost, u, v = heapq.heappop(edges_pq)
            if v not in visited:
                visited.add(v)
                spanning_edges.add(tuple(sorted([u, v])))
                
                # Prevent bathrooms and garages from acting as corridors/pass-throughs
                if not v.startswith('bathroom') and not v.startswith('garage') and v != 'bathroom_social':
                    for neighbor in sorted(graph.edges[v]):
                        if neighbor not in visited:
                            heapq.heappush(edges_pq, (OpeningsPlacer._get_edge_cost(v, neighbor), v, neighbor))

        def get_rank(name):
            if name.startswith('living'): return 0
            if name.startswith('corridor'): return 1
            if name.startswith('kitchen'): return 2
            if name.startswith('bedroom'): return 3
            if name == 'bathroom_social': return 4  # Social bathroom swings into itself
            if name.startswith('bathroom'): return 4
            if name.startswith('garage'): return 5
            return 10

        for edge_id in sorted(spanning_edges):
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
                OpeningsPlacer._add_internal_door_pair(
                    openings_dict, occupied_doors, r1, 'E', r2, 'W',
                    abs_y, y_start, y_end, door_w, 'left'
                )
                continue

            if abs((r2.x + r2.width) - r1.x) < 0.05:
                y_start = max(r1.y, r2.y)
                y_end = min(r1.y + r1.length, r2.y + r2.length)
                overlap = y_end - y_start
                if overlap < door_w: continue
                abs_y = y_start + (overlap - door_w) / 2.0
                OpeningsPlacer._add_internal_door_pair(
                    openings_dict, occupied_doors, r2, 'E', r1, 'W',
                    abs_y, y_start, y_end, door_w, 'left'
                )
                continue

            if abs((r1.y + r1.length) - r2.y) < 0.05:
                x_start = max(r1.x, r2.x)
                x_end = min(r1.x + r1.width, r2.x + r2.width)
                overlap = x_end - x_start
                if overlap < door_w: continue
                abs_x = x_start + (overlap - door_w) / 2.0
                OpeningsPlacer._add_internal_door_pair(
                    openings_dict, occupied_doors, r1, 'N', r2, 'S',
                    abs_x, x_start, x_end, door_w, 'left'
                )
                continue

            if abs((r2.y + r2.length) - r1.y) < 0.05:
                x_start = max(r1.x, r2.x)
                x_end = min(r1.x + r1.width, r2.x + r2.width)
                overlap = x_end - x_start
                if overlap < door_w: continue
                abs_x = x_start + (overlap - door_w) / 2.0
                OpeningsPlacer._add_internal_door_pair(
                    openings_dict, occupied_doors, r1, 'S', r2, 'N',
                    abs_x, x_start, x_end, door_w, 'left'
                )
                continue

        has_main_door = False
        for rspec in plan.rooms:
            if not rspec.exterior_walls:
                continue
            wall_priority = {'S': 0, 'E': 1, 'N': 2, 'W': 3}
            best_walls = sorted(
                rspec.exterior_walls,
                key=lambda e: (
                    -(rspec.width if e in ['S', 'N'] else rspec.length),
                    wall_priority[e],
                ),
            )
            main_ext = best_walls[0]
            wall_length = rspec.width if main_ext in ['S', 'N'] else rspec.length
            boneca = 0.20
            if not has_main_door and rspec.room_type == "living":
                has_main_door = True
                main_w = 0.9
                max_main_offset = wall_length - main_w - boneca
                if max_main_offset >= boneca:
                    main_door, footprint = OpeningsPlacer._resolve_door_opening(
                        rspec,
                        main_ext,
                        boneca,
                        main_w,
                        'right',
                        occupied_doors[rspec.room_type],
                        boneca,
                        max_main_offset,
                    )
                else:
                    main_door = Opening(wall=main_ext, offset=boneca, width=main_w, kind='door', swing='right')
                    footprint = OpeningsPlacer._door_footprint(rspec, main_door)
                openings_dict[rspec.room_type].append(main_door)
                occupied_doors[rspec.room_type].append(footprint)
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
