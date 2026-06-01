from models.floor_plan import FloorPlan, RoomSpec
from core.drawing.openings import Opening
from core.generation.openings_geometry import overlap_area, window_footprint
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


def test_living_main_door_does_not_overlap_window():
    living = RoomSpec(
        "living",
        x=0.0,
        y=0.0,
        width=2.2,
        length=3.0,
        exterior_walls=frozenset({"S"}),
    )
    plan = FloorPlan(seed=1, total_width=2.2, total_length=3.0, rooms=[living])
    graph = SimpleGraph({"living": living}.values(), {"living": set()})

    openings = OpeningsPlacer.generate_openings(plan, graph)
    door = next(opening for opening in openings["living"] if opening.kind == "door")
    window = next(opening for opening in openings["living"] if opening.kind == "window")

    door_footprint = OpeningsPlacer._door_footprint(living, door)
    window_footprint = OpeningsPlacer._window_footprint(living, window)

    assert OpeningsPlacer._overlap_area(door_footprint, window_footprint) == 0.0


def test_window_footprint_overlap_math():
    room = RoomSpec("living", x=0.0, y=0.0, width=3.0, length=3.0)
    first = window_footprint(room, Opening('S', 0.20, 0.80, kind='window'), clearance=0.05)
    overlapping = window_footprint(room, Opening('S', 0.90, 0.80, kind='window'), clearance=0.05)
    separate = window_footprint(room, Opening('S', 1.20, 0.80, kind='window'), clearance=0.05)

    assert overlap_area(first, overlapping) > 0.0
    assert overlap_area(first, separate) == 0.0
