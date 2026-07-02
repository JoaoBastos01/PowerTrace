"""Fase 1: Program — Seleção de cômodos e definição de topologia."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from models.floor_plan import RoomConfig


ROOM_CATALOG: Dict[str, RoomConfig] = {
    "living": RoomConfig(room_type="living", min_area=8.0, max_area=25.0, min_dimension=2.5, requires_natural_light=True, base_probability=1.0, area_threshold=0.0, weight=15.0),
    "kitchen": RoomConfig(room_type="kitchen", min_area=4.0, max_area=15.0, min_dimension=1.5, requires_natural_light=True, base_probability=1.0, area_threshold=0.0, weight=7.0),
    "living_kitchen": RoomConfig(room_type="living_kitchen", min_area=10.0, max_area=22.0, min_dimension=2.5, requires_natural_light=True, base_probability=1.0, area_threshold=0.0, weight=16.0),
    "bathroom_social": RoomConfig(room_type="bathroom_social", min_area=2.4, max_area=4.5, min_dimension=1.35, requires_natural_light=False, base_probability=1.0, area_threshold=0.0, weight=3.0),
    "bathroom_1": RoomConfig(room_type="bathroom_1", min_area=3.2, max_area=6.0, min_dimension=1.45, requires_natural_light=False, base_probability=1.0, area_threshold=0.0, weight=3.5),
    "bathroom_2": RoomConfig(room_type="bathroom_2", min_area=3.2, max_area=5.0, min_dimension=1.45, requires_natural_light=False, base_probability=1.0, area_threshold=0.0, weight=3.0),
    "bedroom_1": RoomConfig(room_type="bedroom_1", min_area=7.0, max_area=20.0, min_dimension=2.5, requires_natural_light=True, base_probability=1.0, area_threshold=0.0, weight=10.0),
    "bedroom_2": RoomConfig(room_type="bedroom_2", min_area=7.0, max_area=16.0, min_dimension=2.5, requires_natural_light=True, base_probability=1.0, area_threshold=0.0, weight=9.0),
    "bedroom_3": RoomConfig(room_type="bedroom_3", min_area=7.0, max_area=14.0, min_dimension=2.5, requires_natural_light=True, base_probability=1.0, area_threshold=0.0, weight=8.0),
    "corridor": RoomConfig(room_type="corridor", min_area=2.0, max_area=6.0, min_dimension=1.0, requires_natural_light=False, base_probability=1.0, area_threshold=0.0, weight=2.5),
    "garage": RoomConfig(room_type="garage", min_area=10.0, max_area=20.0, min_dimension=2.5, requires_natural_light=False, base_probability=1.0, area_threshold=0.0, weight=12.0),
}

CATEGORY_MAX_AREA_OVERRIDES: Dict[str, Dict[str, float]] = {
    "kitnet": {
        "living_kitchen": 29.0,
        "bathroom_1": 6.5,
    },
    "medium": {
        "living": 30.0,
        "kitchen": 16.0,
        "bathroom_social": 5.0,
        "bathroom_1": 6.5,
        "bathroom_2": 5.5,
        "bedroom_1": 21.0,
        "bedroom_2": 18.0,
        "bedroom_3": 16.0,
        "corridor": 7.0,
    },
    "large": {
        "living": 40.0,
        "kitchen": 22.0,
        "bathroom_social": 5.5,
        "bathroom_1": 7.0,
        "bathroom_2": 6.0,
        "bedroom_1": 26.0,
        "bedroom_2": 22.0,
        "bedroom_3": 20.0,
        "corridor": 10.0,
        "garage": 28.0,
    },
}

AREA_EPSILON = 0.05

LARGE_FULL_BATHROOM_SWAP_AREA = 175.0
OPTIONAL_AREA_THRESHOLDS: Dict[Tuple[str, str], float] = {
    ("small", "bedroom_2"): 44.0,
}


def room_max_area(room_type: str, category: str) -> float:
    """Return the realistic maximum area for a room in a house category."""
    category_overrides = CATEGORY_MAX_AREA_OVERRIDES.get(category, {})
    return category_overrides.get(room_type, ROOM_CATALOG[room_type].max_area)


@dataclass(frozen=True)
class TopologyTemplate:
    required: tuple
    optional: tuple
    topology: Dict[str, tuple]


HOUSE_TEMPLATES: Dict[str, TopologyTemplate] = {
    "kitnet": TopologyTemplate(
        required=("living_kitchen", "bathroom_1"), optional=(),
        topology={"living_kitchen": ("bathroom_1",), "bathroom_1": ("living_kitchen",)},
    ),
    "small": TopologyTemplate(
        required=("living", "kitchen", "bathroom_1", "bedroom_1"),
        optional=(("bedroom_2", 0.6),),
        topology={"living": ("kitchen", "bathroom_1", "bedroom_1", "bedroom_2"), "kitchen": ("living",), "bathroom_1": ("living",), "bedroom_1": ("living",), "bedroom_2": ("living",)},
    ),
    "medium": TopologyTemplate(
        required=("living", "kitchen", "corridor", "bathroom_1", "bedroom_1", "bedroom_2"),
        optional=(("bedroom_3", 0.15), ("bathroom_2", 0.35), ("bathroom_social", 0.5)),
        topology={
            "living": ("kitchen", "corridor", "bathroom_social"),
            "kitchen": ("living",),
            "corridor": ("bathroom_1", "bedroom_1", "bedroom_2", "bedroom_3"),
            "bathroom_social": ("living",),
            "bathroom_1": ("corridor",),
            "bedroom_1": ("corridor", "bathroom_2"),
            "bedroom_2": ("corridor",),
            "bedroom_3": ("corridor",),
            "bathroom_2": ("bedroom_1",),
        },
    ),
    "large": TopologyTemplate(
        required=("living", "kitchen", "corridor", "bathroom_social", "bathroom_1", "bedroom_1", "bedroom_2", "bedroom_3", "garage"),
        optional=(("bathroom_2", 0.7),),
        topology={
            "living": ("kitchen", "corridor", "garage", "bathroom_social"),
            "kitchen": ("living",),
            "corridor": ("bathroom_1", "bedroom_1", "bedroom_2", "bedroom_3"),
            "bathroom_social": ("living",),
            "bathroom_1": ("corridor",),
            "bedroom_1": ("corridor", "bathroom_2"),
            "bedroom_2": ("corridor",),
            "bedroom_3": ("corridor",),
            "bathroom_2": ("bedroom_1",),
            "garage": ("living",),
        },
    ),
}


@dataclass
class HouseProgram:
    """Briefing completo da casa: cômodos + topologia + áreas alvo."""
    category: str
    rooms: Dict[str, float]
    topology: Dict[str, List[str]]

    @property
    def topology_edges(self) -> Set[Tuple[str, str]]:
        edges = set()
        for room, neighbors in self.topology.items():
            for neighbor in neighbors:
                edges.add(tuple(sorted([room, neighbor])))
        return edges

    @property
    def root_room(self) -> str:
        if "living" in self.rooms:
            return "living"
        return "living_kitchen"


class ProgramGenerator:
    """Gera o HouseProgram baseado na área total e um RNG determinístico."""

    COMFORT_MARGIN = 4.0

    @staticmethod
    def classify(area: float) -> str:
        if area < 35: return "kitnet"
        elif area < 60: return "small"
        elif area < 100: return "medium"
        else: return "large"

    @staticmethod
    def generate(total_area: float, rng: random.Random) -> HouseProgram:
        category = ProgramGenerator.classify(total_area)
        template = HOUSE_TEMPLATES[category]
        selected = list(template.required)
        selected = ProgramGenerator._adjust_large_bathroom_mix(
            selected,
            total_area,
            category,
        )
        budget = total_area - sum(ROOM_CATALOG[r].min_area for r in selected)
        if budget < 0:
            raise ValueError(f"Área de {total_area}m² insuficiente para casa '{category}'.")
        for room_type, probability in template.optional:
            if room_type in selected:
                continue
            if not ProgramGenerator._optional_room_allowed(
                category,
                room_type,
                total_area,
            ):
                continue
            config = ROOM_CATALOG[room_type]
            cost = config.min_area + ProgramGenerator.COMFORT_MARGIN
            if budget >= cost and rng.random() < probability:
                selected.append(room_type)
                budget -= config.min_area
        selected = ProgramGenerator._ensure_capacity(
            selected,
            [
                room_type
                for room_type, _ in template.optional
                if room_type not in selected
                and ProgramGenerator._optional_room_allowed(
                    category,
                    room_type,
                    total_area,
                )
            ],
            total_area,
            category,
        )
        rooms = ProgramGenerator._allocate_areas(selected, total_area, category)
        topology = ProgramGenerator._prune_topology(template.topology, selected)
        return HouseProgram(category=category, rooms=rooms, topology=topology)

    @staticmethod
    def _ensure_capacity(
        selected: List[str],
        optional_rooms: List[str],
        total_area: float,
        category: str,
    ) -> List[str]:
        selected_with_capacity = list(selected)
        for room_type in optional_rooms:
            if (
                ProgramGenerator._max_capacity(selected_with_capacity, category)
                >= total_area
            ):
                break
            if room_type not in selected_with_capacity:
                selected_with_capacity.append(room_type)

        capacity = ProgramGenerator._max_capacity(selected_with_capacity, category)
        if capacity + AREA_EPSILON < total_area:
            raise ValueError(
                f"Area de {total_area:.1f}m2 excede a capacidade realista "
                f"de {capacity:.1f}m2 para casa '{category}'."
            )

        return selected_with_capacity

    @staticmethod
    def _allocate_areas(
        selected: List[str],
        total_area: float,
        category: str,
    ) -> Dict[str, float]:
        min_total = sum(ROOM_CATALOG[r].min_area for r in selected)
        if min_total - AREA_EPSILON > total_area:
            raise ValueError(
                f"Area de {total_area:.1f}m2 insuficiente para casa '{category}'."
            )

        capacity = ProgramGenerator._max_capacity(selected, category)
        if capacity + AREA_EPSILON < total_area:
            raise ValueError(
                f"Area de {total_area:.1f}m2 excede a capacidade realista "
                f"de {capacity:.1f}m2 para casa '{category}'."
            )

        areas = {room_type: ROOM_CATALOG[room_type].min_area for room_type in selected}
        remaining = total_area - min_total

        while remaining > AREA_EPSILON:
            candidates = [
                room_type
                for room_type in selected
                if (
                    areas[room_type]
                    < room_max_area(room_type, category) - AREA_EPSILON
                )
            ]
            if not candidates:
                break

            total_weight = sum(ROOM_CATALOG[r].weight for r in candidates)
            distributed = 0.0
            for room_type in candidates:
                max_extra = room_max_area(room_type, category) - areas[room_type]
                share = remaining * (ROOM_CATALOG[room_type].weight / total_weight)
                addition = min(share, max_extra)
                areas[room_type] += addition
                distributed += addition

            if distributed <= AREA_EPSILON:
                break
            remaining -= distributed

        if 0 < remaining <= AREA_EPSILON:
            room_type = max(
                selected,
                key=lambda r: room_max_area(r, category) - areas[r],
            )
            headroom = room_max_area(room_type, category) - areas[room_type]
            if headroom + AREA_EPSILON >= remaining:
                areas[room_type] += remaining
                remaining = 0.0

        if remaining > AREA_EPSILON:
            raise ValueError(
                f"Area de {total_area:.1f}m2 excede a capacidade realista "
                f"de {capacity:.1f}m2 para casa '{category}'."
            )

        return areas

    @staticmethod
    def _max_capacity(selected: List[str], category: str) -> float:
        return sum(room_max_area(room_type, category) for room_type in selected)

    @staticmethod
    def _adjust_large_bathroom_mix(
        selected: List[str],
        total_area: float,
        category: str,
    ) -> List[str]:
        if category != "large" or total_area < LARGE_FULL_BATHROOM_SWAP_AREA:
            return selected

        adjusted = [room for room in selected if room != "bathroom_social"]
        if "bathroom_2" not in adjusted:
            adjusted.append("bathroom_2")
        return adjusted

    @staticmethod
    def _optional_room_allowed(
        category: str,
        room_type: str,
        total_area: float,
    ) -> bool:
        threshold = OPTIONAL_AREA_THRESHOLDS.get((category, room_type))
        return threshold is None or total_area >= threshold

    @staticmethod
    def _prune_topology(topology: Dict[str, tuple], selected: List[str]) -> Dict[str, List[str]]:
        selected_set = set(selected)
        pruned = {}
        for room, neighbors in topology.items():
            if room in selected_set:
                pruned[room] = [n for n in neighbors if n in selected_set]
        return pruned
