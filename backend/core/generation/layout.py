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
        left, right = self._split_by_area(rooms, rng)
        left_area = sum(self.program.rooms[r] for r in left)
        right_area = sum(self.program.rooms[r] for r in right)
        ratio = left_area / (left_area + right_area)
        
        # Add slight randomness
        ratio += rng.uniform(-0.05, 0.05)

        # Dynamic physical clamping based on min_dimension
        from .program import ROOM_CATALOG
        min_dim_left = max(ROOM_CATALOG[r].min_dimension for r in left) if left else 1.0
        min_dim_right = max(ROOM_CATALOG[r].min_dimension for r in right) if right else 1.0
        
        horizontal = node.length > node.width
        if abs(node.length - node.width) / max(node.length, node.width) < 0.2:
            if rng.random() < 0.5:
                horizontal = not horizontal
                
        # The dimension being cut
        cut_dim = node.length if horizontal else node.width
        
        # Min ratio to satisfy min_dimension
        min_ratio = min_dim_left / cut_dim
        max_ratio = 1.0 - (min_dim_right / cut_dim)
        
        # If the space is too small to even satisfy the absolute minimums, the partition will fail.
        if min_ratio > max_ratio:
            return False
            
        ratio = max(min_ratio, min(max_ratio, ratio))

        if not node.split(ratio, horizontal, rng):
            if not node.split(ratio, not horizontal, rng):
                return False
        return self._partition(node.left, left, rng) and self._partition(node.right, right, rng)

    def _split_by_area(self, rooms: List[str], rng: random.Random) -> Tuple[List[str], List[str]]:
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
        
        while queue and left_area < half_area * 0.8: # Try to get near half
            curr = queue.pop(0)
            neighbors = [n for n in self.program.topology.get(curr, []) if n in available]
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
        available_list = list(available)
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
            n = list(left)[-1]
            left.remove(n)
            available.add(n)
            
        return list(left), list(available)

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

    # Enforce Corridor Centrality
    if 'corridor' in graph.edges:
        corridor_adjs = graph.edges['corridor']
        # Must connect to the living area
        if 'living' not in corridor_adjs and 'living_kitchen' not in corridor_adjs:
            return False
        
        # Must connect to at least 2 private rooms (bedrooms or bathrooms)
        private_adjs = [r for r in corridor_adjs if r.startswith('bedroom') or r.startswith('bathroom')]
        total_private = sum(1 for r in program.rooms if r.startswith('bedroom') or r.startswith('bathroom'))
        required_private_adjs = min(2, total_private)
        if len(private_adjs) < required_private_adjs:
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
