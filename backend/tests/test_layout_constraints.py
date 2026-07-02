import random

import pytest

from core.generation.bsp import BSPNode
from core.generation.generator import FloorPlanGenerator
from core.generation.layout import AREA_TOLERANCE, validate_topology
from core.generation.program import (
    HouseProgram,
    ProgramGenerator,
    ROOM_CATALOG,
    room_max_area,
)


def _room_signature(plan):
    return [
        (
            room.room_type,
            round(room.x, 8),
            round(room.y, 8),
            round(room.width, 8),
            round(room.length, 8),
            tuple(sorted(room.exterior_walls)),
        )
        for room in plan.rooms
    ]


def test_small_plan_bathrooms_remain_compact():
    for seed in range(30):
        plan, _, _ = FloorPlanGenerator(seed, 5.0, 8.0).generate(max_attempts=300)

        for room in plan.rooms:
            if not room.room_type.startswith("bathroom"):
                continue

            config = ROOM_CATALOG[room.room_type]
            min_side = min(room.width, room.length)
            aspect = max(room.width, room.length) / min_side

            assert min_side >= config.min_dimension
            assert aspect <= 3.5


def test_bathroom_catalog_minimum_widths_avoid_narrow_rooms():
    assert ROOM_CATALOG["bathroom_social"].min_dimension >= 1.35
    assert ROOM_CATALOG["bathroom_1"].min_dimension >= 1.45
    assert ROOM_CATALOG["bathroom_2"].min_dimension >= 1.45


def test_layout_constraints_keep_generation_deterministic():
    first, _, _ = FloorPlanGenerator(12, 5.0, 8.0).generate(max_attempts=300)
    second, _, _ = FloorPlanGenerator(12, 5.0, 8.0).generate(max_attempts=300)

    assert _room_signature(first) == _room_signature(second)


def test_program_area_allocation_respects_category_caps():
    for seed in range(30):
        program = ProgramGenerator.generate(96.0, random.Random(seed))

        assert sum(program.rooms.values()) == pytest.approx(96.0)
        for room_type, area in program.rooms.items():
            assert area <= room_max_area(room_type, program.category)


def test_upper_kitnet_area_remains_supported():
    program = ProgramGenerator.generate(34.0, random.Random(0))

    assert program.category == "kitnet"
    assert sum(program.rooms.values()) == pytest.approx(34.0)
    for room_type, area in program.rooms.items():
        assert area <= room_max_area(room_type, program.category)


def test_large_program_uses_relaxed_living_cap_without_overflowing():
    program = ProgramGenerator.generate(160.0, random.Random(0))

    assert program.category == "large"
    assert program.rooms["living"] > ROOM_CATALOG["living"].max_area
    assert program.rooms["living"] <= room_max_area("living", "large")
    assert sum(program.rooms.values()) == pytest.approx(160.0)


def test_large_180_program_keeps_social_full_bathroom_without_lavabo():
    program = ProgramGenerator.generate(180.0, random.Random(0))

    assert program.category == "large"
    assert "bathroom_1" in program.rooms
    assert "bathroom_2" in program.rooms
    assert "bathroom_social" not in program.rooms
    assert sum(program.rooms.values()) == pytest.approx(180.0)


def test_oversized_large_program_is_rejected():
    with pytest.raises(ValueError, match="capacidade realista"):
        ProgramGenerator.generate(220.0, random.Random(0))


def test_generated_room_areas_stay_within_category_caps():
    scenarios = [
        (8.0, 12.0, range(12), 500),
        (10.0, 16.0, [2, 4, 11, 12, 20], 1500),
    ]
    for width, length, seeds, max_attempts in scenarios:
        for seed in seeds:
            plan, _, program = FloorPlanGenerator(seed, width, length).generate(
                max_attempts=max_attempts
            )

            for room in plan.rooms:
                max_area = room_max_area(room.room_type, program.category)
                assert room.area <= max_area * AREA_TOLERANCE


def test_medium_social_full_bathroom_requires_corridor_adjacency():
    living = BSPNode(0.0, 0.0, 3.0, 3.0)
    living.room_type = "living"
    corridor = BSPNode(0.0, 3.0, 5.0, 1.5)
    corridor.room_type = "corridor"
    bathroom = BSPNode(3.0, 0.0, 1.5, 2.2)
    bathroom.room_type = "bathroom_1"
    bedroom_1 = BSPNode(0.0, 4.5, 2.5, 2.5)
    bedroom_1.room_type = "bedroom_1"
    bedroom_2 = BSPNode(2.5, 4.5, 2.5, 2.5)
    bedroom_2.room_type = "bedroom_2"
    program = HouseProgram(
        category="medium",
        rooms={
            "living": 9.0,
            "corridor": 7.5,
            "bathroom_1": 3.3,
            "bedroom_1": 7.0,
            "bedroom_2": 7.0,
        },
        topology={
            "living": ["corridor"],
            "corridor": ["living", "bathroom_1", "bedroom_1", "bedroom_2"],
            "bathroom_1": ["corridor"],
            "bedroom_1": ["corridor"],
            "bedroom_2": ["corridor"],
        },
    )

    assert (
        validate_topology(
            [living, corridor, bathroom, bedroom_1, bedroom_2],
            program,
        )
        is False
    )
