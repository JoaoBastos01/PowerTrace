"""Fase 2: Layout — BSP guiado pela topologia."""

import random
from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from .bsp import BSPNode
from .program import HouseProgram, ROOM_CATALOG, room_max_area


DEFAULT_MAX_ASPECT = 3.5
AREA_TOLERANCE = 1.05
ROOM_MAX_ASPECT = {
    # A 1.20 m wide bathroom is acceptable only while it remains compact.
    # Wider bathrooms can still be longer, but avoid BSP "noodles" in small plans.
    "bathroom": 3.5,
    "bathroom_social": 3.5,
    "corridor": 12.0,
}


def _max_aspect_for(room_type: str) -> float:
    if room_type.startswith("bathroom"):
        return ROOM_MAX_ASPECT["bathroom"]
    return ROOM_MAX_ASPECT.get(room_type, DEFAULT_MAX_ASPECT)


def _aspect(width: float, length: float) -> float:
    return max(width, length) / min(width, length)


class TopologyBSP:
    """BSP com ordem topológica — procedural mas com viés inteligente."""

    def __init__(self, program: HouseProgram, width: float, length: float):
        self.program = program
        self.width = width
        self.length = length

    def build(self, rng: random.Random) -> Optional[List[BSPNode]]:
        root = BSPNode(0, 0, self.width, self.length)
        ordered = self._bfs_order(rng)
        if not self._partition(root, ordered, rng):
            return None
        return self._leaves(root)

    def _bfs_order(self, rng: random.Random) -> List[str]:
        root = self.program.root_room
        visited: Set[str] = set()
        order: List[str] = []
        queue = deque([root])
        while queue:
            room = queue.popleft()
            if room in visited:
                continue
            visited.add(room)
            order.append(room)
            neighbors = list(self.program.topology.get(room, []))
            rng.shuffle(neighbors)
            for n in neighbors:
                if n not in visited:
                    queue.append(n)
        return order

    def _partition(self, node: BSPNode, rooms: List[str], rng: random.Random) -> bool:
        if len(rooms) == 1:
            node.room_type = rooms[0]
            return True
        left, right = self._split_by_area(rooms, rng)
        left_area = sum(self.program.rooms[r] for r in left)
        right_area = sum(self.program.rooms[r] for r in right)
        ratio = left_area / (left_area + right_area)

        # Add slight randomness
        ratio += rng.uniform(-0.05, 0.05)

        horizontal, ratio = self._choose_split_axis(node, left, right, ratio, rng)
        if horizontal is None:
            return False

        if not node.split(ratio, horizontal, rng):
            if not node.split(ratio, not horizontal, rng):
                return False
        return self._partition(node.left, left, rng) and self._partition(
            node.right, right, rng
        )

    def _choose_split_axis(
        self,
        node: BSPNode,
        left: List[str],
        right: List[str],
        ratio: float,
        rng: random.Random,
    ) -> Tuple[Optional[bool], float]:
        candidates = []
        for horizontal in (True, False):
            cut_dim = node.length if horizontal else node.width
            if cut_dim <= 0:
                continue

            min_dim_left = max(ROOM_CATALOG[r].min_dimension for r in left) if left else 1.0
            min_dim_right = max(ROOM_CATALOG[r].min_dimension for r in right) if right else 1.0
            min_ratio = min_dim_left / cut_dim
            max_ratio = 1.0 - (min_dim_right / cut_dim)
            area_min_ratio, area_max_ratio = self._area_ratio_bounds(node, left, right)
            min_ratio = max(min_ratio, area_min_ratio)
            max_ratio = min(max_ratio, area_max_ratio)
            if min_ratio > max_ratio:
                continue

            clamped = max(min_ratio, min(max_ratio, ratio))
            left_w, left_l, right_w, right_l = self._split_dimensions(node, clamped, horizontal)
            if not self._terminal_rooms_fit(left, left_w, left_l):
                continue
            if not self._terminal_rooms_fit(right, right_w, right_l):
                continue

            worst_aspect = max(_aspect(left_w, left_l), _aspect(right_w, right_l))
            clamp_penalty = abs(clamped - ratio)
            candidates.append((worst_aspect, clamp_penalty, horizontal, clamped))

        if not candidates:
            return None, ratio

        candidates.sort(key=lambda item: (item[0], item[1], not item[2]))
        best_aspect, _, horizontal, clamped = candidates[0]

        # Preserve the previous procedural variety when both axes are comparably good.
        if len(candidates) > 1 and abs(best_aspect - candidates[1][0]) < 1.0 and rng.random() < 0.3:
            _, _, horizontal, clamped = candidates[1]

        return horizontal, clamped

    def _split_dimensions(
        self, node: BSPNode, ratio: float, horizontal: bool
    ) -> Tuple[float, float, float, float]:
        if horizontal:
            left_l = node.length * ratio
            return node.width, left_l, node.width, node.length - left_l
        left_w = node.width * ratio
        return left_w, node.length, node.width - left_w, node.length

    def _area_ratio_bounds(
        self,
        node: BSPNode,
        left: List[str],
        right: List[str],
    ) -> Tuple[float, float]:
        node_area = node.width * node.length
        left_min = sum(ROOM_CATALOG[r].min_area for r in left)
        left_max = sum(
            room_max_area(r, self.program.category) * AREA_TOLERANCE
            for r in left
        )
        right_min = sum(ROOM_CATALOG[r].min_area for r in right)
        right_max = sum(
            room_max_area(r, self.program.category) * AREA_TOLERANCE
            for r in right
        )

        min_ratio = max(left_min / node_area, 1.0 - (right_max / node_area))
        max_ratio = min(left_max / node_area, 1.0 - (right_min / node_area))
        return min_ratio, max_ratio

    def _terminal_rooms_fit(self, rooms: List[str], width: float, length: float) -> bool:
        if len(rooms) != 1:
            return True
        room_type = rooms[0]
        config = ROOM_CATALOG[room_type]
        if min(width, length) < config.min_dimension:
            return False
        if width * length > room_max_area(room_type, self.program.category) * AREA_TOLERANCE:
            return False
        return _aspect(width, length) <= _max_aspect_for(room_type)

    def _split_by_area(
        self, rooms: List[str], rng: random.Random
    ) -> Tuple[List[str], List[str]]:
        # If 2 rooms, just split them
        if len(rooms) <= 2:
            return [rooms[0]], rooms[1:]

        total_area = sum(self.program.rooms[r] for r in rooms)
        half_area = total_area / 2.0

        # Start with a random room as the seed for the left group
        seed_room = rng.choice(rooms)
        left = {seed_room}
        left_area = self.program.rooms[seed_room]

        # BFS to grow the left group using topology, keeping it connected
        queue = [seed_room]
        available = set(rooms) - {seed_room}

        while queue and left_area < half_area * 0.8:  # Try to get near half
            curr = queue.pop(0)
            neighbors = [
                n for n in self.program.topology.get(curr, []) if n in available
            ]
            rng.shuffle(neighbors)

            for n in neighbors:
                if left_area >= half_area:
                    break
                left.add(n)
                left_area += self.program.rooms[n]
                available.remove(n)
                queue.append(n)

        # If we couldn't reach half area using topology (graph disconnected or sparse)
        # Just add random available rooms to balance it
        available_list = sorted(available)
        rng.shuffle(available_list)
        for n in available_list:
            if left_area >= half_area:
                break
            left.add(n)
            left_area += self.program.rooms[n]
            available.remove(n)

        # Ensure we don't have empty groups
        if not left:
            left.add(available_list[0])
            available.remove(available_list[0])
        elif not available:
            n = sorted(left)[-1]
            left.remove(n)
            available.add(n)

        return sorted(left), sorted(available)

    def _leaves(self, node: BSPNode) -> List[BSPNode]:
        if node.is_leaf():
            return [node]
        out: List[BSPNode] = []
        if node.left:
            out.extend(self._leaves(node.left))
        if node.right:
            out.extend(self._leaves(node.right))
        return out


def validate_topology(leaves: List[BSPNode], program: HouseProgram) -> bool:
    """Verifica se o layout satisfaz topologia + regras de sanidade."""
    from .adjacency import AdjacencyGraph

    graph = AdjacencyGraph(leaves)
    if not graph.validate_architecture():
        import logging

        logging.getLogger(__name__).debug("Edge falhou: arquitetura inválida")
        return False
    nodes: Dict[str, BSPNode] = {l.room_type: l for l in leaves if l.room_type}
    baths = [rt for rt in nodes if rt.startswith("bathroom")]
    for i in range(len(baths)):
        for j in range(i + 1, len(baths)):
            if _adjacent(nodes[baths[i]], nodes[baths[j]], 0.05):
                return False

    # Enforce Corridor Centrality
    if "corridor" in graph.edges:
        corridor_adjs = graph.edges["corridor"]
        # Must connect to the living area
        if "living" not in corridor_adjs and "living_kitchen" not in corridor_adjs:
            return False

        # Must connect to at least 2 private rooms (bedrooms or bathrooms)
        private_adjs = [
            r
            for r in corridor_adjs
            if r.startswith("bedroom") or r.startswith("bathroom")
        ]
        total_private = sum(
            1
            for r in program.rooms
            if r.startswith("bedroom") or r.startswith("bathroom")
        )
        required_private_adjs = min(2, total_private)
        if len(private_adjs) < required_private_adjs:
            return False

    if program.category in {"medium", "large"} and "bathroom_1" in graph.edges:
        if "corridor" not in graph.edges["bathroom_1"]:
            return False

    # Enforce realistic aspect ratios for rooms (prevent noodles)
    for node in leaves:
        config = ROOM_CATALOG.get(node.room_type)
        if config and node.width * node.length > room_max_area(node.room_type, program.category) * AREA_TOLERANCE:
            return False

        if node.room_type == 'corridor':
            continue
        if config and min(node.width, node.length) < config.min_dimension:
            return False

        if _aspect(node.width, node.length) > _max_aspect_for(node.room_type):
            return False

    return True


def _adjacent(n1: BSPNode, n2: BSPNode, min_overlap: float) -> bool:
    EPS = 0.05
    if abs((n1.x + n1.width) - n2.x) < EPS or abs((n2.x + n2.width) - n1.x) < EPS:
        ov = min(n1.y + n1.length, n2.y + n2.length) - max(n1.y, n2.y)
        if ov >= min_overlap:
            return True
    if abs((n1.y + n1.length) - n2.y) < EPS or abs((n2.y + n2.length) - n1.y) < EPS:
        ov = min(n1.x + n1.width, n2.x + n2.width) - max(n1.x, n2.x)
        if ov >= min_overlap:
            return True
    return False
