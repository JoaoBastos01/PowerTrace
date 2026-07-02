"""Módulo de Posicionamento Lógico de Aberturas (Portas e Janelas)."""

from typing import Dict, List, Tuple
from models.floor_plan import FloorPlan
from core.drawing.openings import Opening
from core.generation.adjacency import AdjacencyGraph
from core.generation.access_policy import build_access_edges, connection_cost
from core.generation.openings_geometry import (
    Rect,
    absolute_start_from_opening,
    door_footprint,
    offset_bounds_from_absolute_span,
    offset_from_absolute_start,
    overlap_area,
    wall_length,
    wall_points,
    window_footprint,
)
from core.generation.openings_resolution import (
    offset_candidates,
    resolve_door_opening,
    resolve_exterior_window,
    resolve_window_opening,
    swing_candidates,
)


class OpeningsPlacer:
    """Distribui portas e janelas com base no grafo de intersecções."""

    DOOR_CANDIDATE_STEP = 0.20
    DOOR_CLEARANCE = 0.05
    WINDOW_MIN_WIDTH = 0.40

    @staticmethod
    def _get_edge_cost(r1: str, r2: str, category: str | None = None) -> int:
        """Determina o custo arquitetonico de conectar dois comodos."""
        return connection_cost(r1, r2, category)

    @staticmethod
    def _wall_points(room, wall: str) -> Tuple[tuple, tuple]:
        return wall_points(room, wall)

    @staticmethod
    def _offset_from_absolute_start(room, wall: str, absolute_start: float, width: float) -> float:
        return offset_from_absolute_start(room, wall, absolute_start, width)

    @staticmethod
    def _absolute_start_from_opening(room, opening: Opening) -> float:
        return absolute_start_from_opening(room, opening)

    @staticmethod
    def _offset_bounds_from_absolute_span(
        room,
        wall: str,
        absolute_min: float,
        absolute_max: float,
        width: float,
    ) -> Tuple[float, float]:
        return offset_bounds_from_absolute_span(room, wall, absolute_min, absolute_max, width)

    @staticmethod
    def _offset_candidates(preferred: float, minimum: float, maximum: float) -> List[float]:
        return offset_candidates(preferred, minimum, maximum, OpeningsPlacer.DOOR_CANDIDATE_STEP)

    @staticmethod
    def _swing_candidates(preferred: str) -> List[str]:
        return swing_candidates(preferred)

    @staticmethod
    def _door_footprint(room, opening: Opening) -> Tuple[float, float, float, float]:
        return door_footprint(room, opening, OpeningsPlacer.DOOR_CLEARANCE)

    @staticmethod
    def _window_footprint(room, opening: Opening) -> Tuple[float, float, float, float]:
        return window_footprint(room, opening, OpeningsPlacer.DOOR_CLEARANCE)

    @staticmethod
    def _overlap_area(
        first: Tuple[float, float, float, float],
        second: Tuple[float, float, float, float],
    ) -> float:
        return overlap_area(first, second)

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
        return resolve_door_opening(
            room,
            wall,
            preferred_offset,
            width,
            preferred_swing,
            occupied_footprints,
            minimum_offset,
            maximum_offset,
            OpeningsPlacer.DOOR_CANDIDATE_STEP,
            OpeningsPlacer.DOOR_CLEARANCE,
        )

    @staticmethod
    def _resolve_window_opening(
        room,
        wall: str,
        preferred_offset: float,
        width: float,
        occupied_footprints: List[Tuple[float, float, float, float]],
        minimum_offset: float,
        maximum_offset: float,
    ) -> Opening | None:
        return resolve_window_opening(
            room,
            wall,
            preferred_offset,
            width,
            occupied_footprints,
            minimum_offset,
            maximum_offset,
            OpeningsPlacer.DOOR_CANDIDATE_STEP,
            OpeningsPlacer.DOOR_CLEARANCE,
            OpeningsPlacer.WINDOW_MIN_WIDTH,
        )

    @staticmethod
    def _resolve_exterior_window(
        room,
        wall: str,
        preferred_offset: float,
        preferred_width: float,
        occupied_footprints: List[Tuple[float, float, float, float]],
        min_margin: float,
    ) -> Opening | None:
        return resolve_exterior_window(
            room,
            wall,
            preferred_offset,
            preferred_width,
            occupied_footprints,
            min_margin,
            OpeningsPlacer.DOOR_CANDIDATE_STEP,
            OpeningsPlacer.DOOR_CLEARANCE,
            OpeningsPlacer.WINDOW_MIN_WIDTH,
        )

    @staticmethod
    def _add_internal_door_pair(
        openings_dict: Dict[str, List[Opening]],
        occupied_footprints: Dict[str, List[Rect]],
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
            occupied_footprints[door_room.room_type],
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
        occupied_footprints[door_room.room_type].append(footprint)

    @staticmethod
    def generate_openings(plan: FloorPlan, graph: AdjacencyGraph, program=None) -> Dict[str, List[Opening]]:
        """Gera o dicionário injetável de Openings para o DXFGenerator."""
        openings_dict: Dict[str, List[Opening]] = {rspec.room_type: [] for rspec in plan.rooms}
        occupied_footprints: Dict[str, List[Rect]] = {
            rspec.room_type: [] for rspec in plan.rooms
        }
        category = getattr(program, "category", None)
        access_edges = (
            build_access_edges(graph.edges, program.topology_edges, category)
            if program is not None
            else graph.edges
        )
        # Build MST (Prim's algorithm) to guarantee access with minimum architectural cost
        root_room = 'living' if any(r.room_type == 'living' for r in plan.rooms) else 'living_kitchen'
        if not any(r.room_type == root_room for r in plan.rooms):
            root_room = plan.rooms[0].room_type

        visited = {root_room}
        spanning_edges = set()
        import heapq
        
        edges_pq = []
        for neighbor in sorted(access_edges[root_room]):
            heapq.heappush(edges_pq, (OpeningsPlacer._get_edge_cost(root_room, neighbor, category), root_room, neighbor))
            
        while edges_pq:
            cost, u, v = heapq.heappop(edges_pq)
            if v not in visited:
                visited.add(v)
                spanning_edges.add(tuple(sorted([u, v])))
                
                # Prevent bathrooms and garages from acting as corridors/pass-throughs
                if not v.startswith('bathroom') and not v.startswith('garage') and v != 'bathroom_social':
                    for neighbor in sorted(access_edges[v]):
                        if neighbor not in visited:
                            heapq.heappush(edges_pq, (OpeningsPlacer._get_edge_cost(v, neighbor, category), v, neighbor))

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
                    openings_dict, occupied_footprints, r1, 'E', r2, 'W',
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
                    openings_dict, occupied_footprints, r2, 'E', r1, 'W',
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
                    openings_dict, occupied_footprints, r1, 'N', r2, 'S',
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
                    openings_dict, occupied_footprints, r1, 'S', r2, 'N',
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
            ext_wall_length = wall_length(rspec, main_ext)
            boneca = 0.20
            if not has_main_door and rspec.room_type == "living":
                has_main_door = True
                main_w = 0.9
                max_main_offset = ext_wall_length - main_w - boneca
                if max_main_offset >= boneca:
                    main_door, footprint = OpeningsPlacer._resolve_door_opening(
                        rspec,
                        main_ext,
                        boneca,
                        main_w,
                        'right',
                        occupied_footprints[rspec.room_type],
                        boneca,
                        max_main_offset,
                    )
                else:
                    main_door = Opening(wall=main_ext, offset=boneca, width=main_w, kind='door', swing='right')
                    footprint = OpeningsPlacer._door_footprint(rspec, main_door)
                openings_dict[rspec.room_type].append(main_door)
                occupied_footprints[rspec.room_type].append(footprint)
                win_w = 1.2
                win_off = (ext_wall_length / 2) - (win_w / 2)
                if win_off < (boneca + main_w + 0.3):
                    win_off = ext_wall_length - win_w - 0.2
                window = OpeningsPlacer._resolve_exterior_window(
                    rspec,
                    main_ext,
                    win_off,
                    win_w,
                    occupied_footprints[rspec.room_type],
                    boneca,
                )
                if window:
                    openings_dict[rspec.room_type].append(window)
            elif rspec.room_type == 'garage':
                door_w = 2.5
                if ext_wall_length >= door_w + 0.4:
                    door_off = (ext_wall_length / 2) - (door_w / 2)
                    openings_dict[rspec.room_type].append(Opening(wall=main_ext, offset=door_off, width=door_w, kind='garage_door', swing='left'))
            else:
                win_w = 1.2
                if rspec.room_type.startswith("bathroom"):
                    win_w = 0.60
                
                # Minimum margin required (0.15m wall + 0.05m inner boneca)
                min_margin = 0.20
                if ext_wall_length < win_w + 2 * min_margin:
                    win_w = ext_wall_length - 2 * min_margin
                
                if win_w >= OpeningsPlacer.WINDOW_MIN_WIDTH:
                    win_off = (ext_wall_length / 2) - (win_w / 2)
                    window = OpeningsPlacer._resolve_exterior_window(
                        rspec,
                        main_ext,
                        win_off,
                        win_w,
                        occupied_footprints[rspec.room_type],
                        min_margin,
                    )
                    if window:
                        openings_dict[rspec.room_type].append(window)

        return openings_dict
