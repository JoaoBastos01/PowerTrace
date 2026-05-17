"""Fase 2: Layout — BSP guiado pela topologia."""

import random
from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from .bsp import BSPNode
from .program import HouseProgram


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
        left, right = self._split_by_area(rooms)
        left_area = sum(self.program.rooms[r] for r in left)
        right_area = sum(self.program.rooms[r] for r in right)
        ratio = left_area / (left_area + right_area)
        ratio += rng.uniform(-0.05, 0.05)
        ratio = max(0.2, min(0.8, ratio))
        horizontal = node.length > node.width
        if abs(node.length - node.width) / max(node.length, node.width) < 0.2:
            if rng.random() < 0.5:
                horizontal = not horizontal
        if not node.split(ratio, horizontal, rng):
            if not node.split(ratio, not horizontal, rng):
                return False
        return self._partition(node.left, left, rng) and self._partition(node.right, right, rng)

    def _split_by_area(self, rooms: List[str]) -> Tuple[List[str], List[str]]:
        total = sum(self.program.rooms[r] for r in rooms)
        half = total / 2.0
        accumulated = 0.0
        idx = 1
        for i, room in enumerate(rooms):
            accumulated += self.program.rooms[room]
            if accumulated >= half and i > 0:
                idx = i
                break
        idx = max(1, min(idx, len(rooms) - 1))
        return rooms[:idx], rooms[idx:]

    def _leaves(self, node: BSPNode) -> List[BSPNode]:
        if node.is_leaf():
            return [node]
        out: List[BSPNode] = []
        if node.left: out.extend(self._leaves(node.left))
        if node.right: out.extend(self._leaves(node.right))
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
    return True


def _adjacent(n1: BSPNode, n2: BSPNode, min_overlap: float) -> bool:
    EPS = 0.05
    if abs((n1.x + n1.width) - n2.x) < EPS or abs((n2.x + n2.width) - n1.x) < EPS:
        ov = min(n1.y + n1.length, n2.y + n2.length) - max(n1.y, n2.y)
        if ov >= min_overlap: return True
    if abs((n1.y + n1.length) - n2.y) < EPS or abs((n2.y + n2.length) - n1.y) < EPS:
        ov = min(n1.x + n1.width, n2.x + n2.width) - max(n1.x, n2.x)
        if ov >= min_overlap: return True
    return False
