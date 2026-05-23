"""Algoritmo Zoned BSP para o FloorPlan."""

import random
from typing import Dict, List, Optional, Set


class BSPNode:
    """Representa uma fatia retangular do terreno/planta."""
    def __init__(self, x: float, y: float, w: float, l: float, exterior_walls: Set[str] = None):
        self.x = x
        self.y = y
        self.width = w
        self.length = l
        self.exterior_walls = exterior_walls if exterior_walls is not None else {'N', 'S', 'E', 'W'}
        self.room_type: Optional[str] = None
        self.left: Optional['BSPNode'] = None
        self.right: Optional['BSPNode'] = None

    def is_leaf(self) -> bool:
        return self.left is None and self.right is None

    def split(self, split_ratio: float, horizontal: bool, rng: random.Random) -> bool:
        """Subdivide este container em dois menores usando uma proporção da área."""
        MIN_DIM = 1.0

        if horizontal:
            split_length = self.length * split_ratio
            if split_length < MIN_DIM or (self.length - split_length) < MIN_DIM:
                return False
            left_ext = set(self.exterior_walls)
            if 'N' in left_ext: left_ext.remove('N')
            right_ext = set(self.exterior_walls)
            if 'S' in right_ext: right_ext.remove('S')
            self.left = BSPNode(self.x, self.y, self.width, split_length, left_ext)
            self.right = BSPNode(self.x, self.y + split_length, self.width, self.length - split_length, right_ext)
        else:
            split_width = self.width * split_ratio
            if split_width < MIN_DIM or (self.width - split_width) < MIN_DIM:
                return False
            left_ext = set(self.exterior_walls)
            if 'E' in left_ext: left_ext.remove('E')
            right_ext = set(self.exterior_walls)
            if 'W' in right_ext: right_ext.remove('W')
            self.left = BSPNode(self.x, self.y, split_width, self.length, left_ext)
            self.right = BSPNode(self.x + split_width, self.y, self.width - split_width, self.length, right_ext)

        return True


class BSPTreeGenerator:
    """Orquestrador do Zoned BSP."""

    def __init__(self, target_areas: Dict[str, float], total_w: float, total_l: float):
        self.target_areas = target_areas
        self.total_w = total_w
        self.total_l = total_l

    def build_tree(self, rng: random.Random) -> Optional[List[BSPNode]]:
        """Executa o fatiamento guiado pelas áreas alvo."""
        root = BSPNode(0, 0, self.total_w, self.total_l)

        social_rooms = {k: v for k, v in self.target_areas.items() if k in ["living", "kitchen", "garage"]}
        intimate_rooms = {k: v for k, v in self.target_areas.items() if k not in social_rooms}

        social_area = sum(social_rooms.values())
        intimate_area = sum(intimate_rooms.values())
        total_area = social_area + intimate_area

        if intimate_area > 0 and social_area > 0:
            horizontal_cut = rng.choice([True, False])
            split_ratio = social_area / total_area
            if not root.split(split_ratio, horizontal_cut, rng):
                horizontal_cut = not horizontal_cut
                if not root.split(split_ratio, horizontal_cut, rng):
                    return None
            if not self._partition_node(root.left, social_rooms, rng): return None
            if not self._partition_node(root.right, intimate_rooms, rng): return None
        else:
            if not self._partition_node(root, self.target_areas, rng): return None

        return self._collect_leaves(root)

    def _partition_node(self, node: BSPNode, rooms: Dict[str, float], rng: random.Random) -> bool:
        room_keys = sorted(rooms.keys())
        if len(room_keys) == 1:
            node.room_type = room_keys[0]
            return True
        rng.shuffle(room_keys)
        mid = len(room_keys) // 2
        left_keys = room_keys[:mid]
        right_keys = room_keys[mid:]
        left_area = sum(rooms[k] for k in left_keys)
        right_area = sum(rooms[k] for k in right_keys)
        split_ratio = left_area / (left_area + right_area)
        horizontal_cut = node.length > node.width
        if not node.split(split_ratio, horizontal=horizontal_cut, rng=rng):
            if not node.split(split_ratio, horizontal=not horizontal_cut, rng=rng):
                return False
        left_rooms = {k: rooms[k] for k in left_keys}
        right_rooms = {k: rooms[k] for k in right_keys}
        if not self._partition_node(node.left, left_rooms, rng): return None
        if not self._partition_node(node.right, right_rooms, rng): return None
        return True

    def _collect_leaves(self, node: BSPNode) -> List[BSPNode]:
        if node.is_leaf():
            return [node]
        leaves = []
        if node.left: leaves.extend(self._collect_leaves(node.left))
        if node.right: leaves.extend(self._collect_leaves(node.right))
        return leaves
