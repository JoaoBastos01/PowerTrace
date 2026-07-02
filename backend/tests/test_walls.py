from core.drawing.openings import Opening
from core.drawing.walls import draw_room_structure
from core.electrical.rooms import Living


class FakeModelspace:
    def __init__(self):
        self.lines = []
        self.arcs = []

    def add_line(self, start, end, dxfattribs=None):
        self.lines.append((start, end, dxfattribs or {}))

    def add_arc(self, center, radius, start_angle, end_angle, dxfattribs=None):
        self.arcs.append((center, radius, start_angle, end_angle, dxfattribs or {}))


def test_inner_door_gap_near_corner_is_clamped_to_inner_wall():
    msp = FakeModelspace()
    room = Living(name="Sala", width=3.0, length=3.0, origin=(0.0, 0.0))
    room.exterior_walls = {"N", "S", "E", "W"}

    draw_room_structure(
        msp,
        room,
        openings=[Opening(wall="S", offset=0.02, width=0.8, kind="door")],
    )

    inner_wall_lines = [
        (start, end)
        for start, end, attrs in msp.lines
        if attrs.get("layer") == "PT_WALLS_INNER"
    ]
    assert inner_wall_lines

    xs = [point[0] for line in inner_wall_lines for point in line]
    assert min(xs) >= 0.15 - 1e-9
