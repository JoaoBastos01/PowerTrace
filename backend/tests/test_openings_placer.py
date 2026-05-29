from models.floor_plan import FloorPlan, RoomSpec
from core.generation.openings_placer import OpeningsPlacer


class SimpleGraph:
    def __init__(self, rooms, edges):
        self.rooms = {room.room_type: room for room in rooms}
        self.edges = edges


def _opening_signature(openings):
    return {
        room_type: [
            (
                opening.wall,
                round(opening.offset, 8),
                round(opening.width, 8),
                opening.kind,
                opening.swing,
            )
            for opening in room_openings
        ]
        for room_type, room_openings in sorted(openings.items())
    }


def test_internal_door_footprints_do_not_overlap_in_same_room():
    living = RoomSpec("living", x=-1.0, y=1.0, width=2.0, length=2.0)
    corridor = RoomSpec("corridor", x=1.0, y=-1.0, width=2.0, length=2.0)
    bedroom = RoomSpec("bedroom_1", x=1.0, y=1.0, width=2.0, length=2.0)
    rooms = [living, corridor, bedroom]
    plan = FloorPlan(seed=1, total_width=4.0, total_length=4.0, rooms=rooms)
    graph = SimpleGraph(
        rooms,
        {
            "living": {"bedroom_1"},
            "corridor": {"bedroom_1"},
            "bedroom_1": {"living", "corridor"},
        },
    )

    openings = OpeningsPlacer.generate_openings(plan, graph)
    bedroom_doors = [
        opening for opening in openings["bedroom_1"] if opening.kind == "door"
    ]

    assert len(bedroom_doors) == 2
    footprints = [
        OpeningsPlacer._door_footprint(bedroom, opening)
        for opening in bedroom_doors
    ]
    assert OpeningsPlacer._overlap_area(footprints[0], footprints[1]) == 0.0


def test_door_collision_resolution_is_deterministic():
    living = RoomSpec("living", x=-1.0, y=1.0, width=2.0, length=2.0)
    corridor = RoomSpec("corridor", x=1.0, y=-1.0, width=2.0, length=2.0)
    bedroom = RoomSpec("bedroom_1", x=1.0, y=1.0, width=2.0, length=2.0)
    rooms = [living, corridor, bedroom]
    plan = FloorPlan(seed=1, total_width=4.0, total_length=4.0, rooms=rooms)
    graph = SimpleGraph(
        rooms,
        {
            "living": {"bedroom_1"},
            "corridor": {"bedroom_1"},
            "bedroom_1": {"living", "corridor"},
        },
    )

    signatures = [
        _opening_signature(OpeningsPlacer.generate_openings(plan, graph))
        for _ in range(5)
    ]

    assert signatures == [signatures[0]] * len(signatures)
