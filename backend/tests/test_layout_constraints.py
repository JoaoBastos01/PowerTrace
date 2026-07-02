from core.generation.generator import FloorPlanGenerator
from core.generation.program import ROOM_CATALOG


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


def test_layout_constraints_keep_generation_deterministic():
    first, _, _ = FloorPlanGenerator(12, 5.0, 8.0).generate(max_attempts=300)
    second, _, _ = FloorPlanGenerator(12, 5.0, 8.0).generate(max_attempts=300)

    assert _room_signature(first) == _room_signature(second)
