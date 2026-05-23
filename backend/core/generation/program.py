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
    "bathroom_social": RoomConfig(room_type="bathroom_social", min_area=2.0, max_area=4.5, min_dimension=1.2, requires_natural_light=False, base_probability=1.0, area_threshold=0.0, weight=3.0),
    "bathroom_1": RoomConfig(room_type="bathroom_1", min_area=2.5, max_area=6.0, min_dimension=1.2, requires_natural_light=False, base_probability=1.0, area_threshold=0.0, weight=3.5),
    "bathroom_2": RoomConfig(room_type="bathroom_2", min_area=2.5, max_area=5.0, min_dimension=1.2, requires_natural_light=False, base_probability=1.0, area_threshold=0.0, weight=3.0),
    "bedroom_1": RoomConfig(room_type="bedroom_1", min_area=7.0, max_area=20.0, min_dimension=2.5, requires_natural_light=True, base_probability=1.0, area_threshold=0.0, weight=10.0),
    "bedroom_2": RoomConfig(room_type="bedroom_2", min_area=7.0, max_area=16.0, min_dimension=2.5, requires_natural_light=True, base_probability=1.0, area_threshold=0.0, weight=9.0),
    "bedroom_3": RoomConfig(room_type="bedroom_3", min_area=7.0, max_area=14.0, min_dimension=2.5, requires_natural_light=True, base_probability=1.0, area_threshold=0.0, weight=8.0),
    "corridor": RoomConfig(room_type="corridor", min_area=2.0, max_area=6.0, min_dimension=1.0, requires_natural_light=False, base_probability=1.0, area_threshold=0.0, weight=2.5),
    "garage": RoomConfig(room_type="garage", min_area=10.0, max_area=20.0, min_dimension=2.5, requires_natural_light=False, base_probability=1.0, area_threshold=0.0, weight=12.0),
}


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
        budget = total_area - sum(ROOM_CATALOG[r].min_area for r in selected)
        if budget < 0:
            raise ValueError(f"Área de {total_area}m² insuficiente para casa '{category}'.")
        for room_type, probability in template.optional:
            config = ROOM_CATALOG[room_type]
            cost = config.min_area + ProgramGenerator.COMFORT_MARGIN
            if budget >= cost and rng.random() < probability:
                selected.append(room_type)
                budget -= config.min_area
        rooms = ProgramGenerator._allocate_areas(selected, total_area)
        topology = ProgramGenerator._prune_topology(template.topology, selected)
        return HouseProgram(category=category, rooms=rooms, topology=topology)

    @staticmethod
    def _allocate_areas(selected: List[str], total_area: float) -> Dict[str, float]:
        configs = [ROOM_CATALOG[r] for r in selected]
        total_weight = sum(c.weight for c in configs)
        areas = {}
        allocated = 0.0
        for conf in configs:
            raw = (conf.weight / total_weight) * total_area
            clamped = max(conf.min_area, min(raw, conf.max_area))
            areas[conf.room_type] = clamped
            allocated += clamped
        diff = total_area - allocated
        if abs(diff) > 0.1:
            primary = "living" if "living" in areas else "living_kitchen"
            if primary in areas:
                areas[primary] += diff
            else:
                bump = diff / len(areas)
                for r in areas:
                    areas[r] += bump
        return areas

    @staticmethod
    def _prune_topology(topology: Dict[str, tuple], selected: List[str]) -> Dict[str, List[str]]:
        selected_set = set(selected)
        pruned = {}
        for room, neighbors in topology.items():
            if room in selected_set:
                pruned[room] = [n for n in neighbors if n in selected_set]
        return pruned
