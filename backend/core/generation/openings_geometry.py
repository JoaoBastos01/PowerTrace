"""Pure geometry helpers for generated doors and windows."""

import math
from typing import Tuple

from core.drawing.openings import Opening

Rect = Tuple[float, float, float, float]


def wall_points(room, wall: str) -> Tuple[tuple, tuple]:
    x, y = room.x, room.y
    w, l = room.width, room.length
    return {
        'S': ((x, y), (x + w, y)),
        'E': ((x + w, y), (x + w, y + l)),
        'N': ((x + w, y + l), (x, y + l)),
        'W': ((x, y + l), (x, y)),
    }[wall]


def wall_length(room, wall: str) -> float:
    return room.width if wall in ['S', 'N'] else room.length


def offset_from_absolute_start(room, wall: str, absolute_start: float, width: float) -> float:
    if wall == 'E':
        return absolute_start - room.y
    if wall == 'W':
        return (room.y + room.length) - (absolute_start + width)
    if wall == 'S':
        return absolute_start - room.x
    return (room.x + room.width) - (absolute_start + width)


def absolute_start_from_opening(room, opening: Opening) -> float:
    if opening.wall == 'E':
        return room.y + opening.offset
    if opening.wall == 'W':
        return room.y + room.length - opening.offset - opening.width
    if opening.wall == 'S':
        return room.x + opening.offset
    return room.x + room.width - opening.offset - opening.width


def offset_bounds_from_absolute_span(
    room,
    wall: str,
    absolute_min: float,
    absolute_max: float,
    width: float,
) -> Tuple[float, float]:
    first = offset_from_absolute_start(room, wall, absolute_min, width)
    last = offset_from_absolute_start(room, wall, absolute_max, width)
    return min(first, last), max(first, last)


def door_footprint(room, opening: Opening, clearance: float) -> Rect:
    wall_start, wall_end = wall_points(room, opening.wall)
    dx = wall_end[0] - wall_start[0]
    dy = wall_end[1] - wall_start[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return (wall_start[0], wall_start[1], wall_start[0], wall_start[1])

    ux, uy = dx / length, dy / length
    in_x, in_y = -uy, ux
    closed_start = (
        wall_start[0] + ux * opening.offset,
        wall_start[1] + uy * opening.offset,
    )
    closed_end = (
        wall_start[0] + ux * (opening.offset + opening.width),
        wall_start[1] + uy * (opening.offset + opening.width),
    )
    hinge = closed_start if opening.swing == 'right' else closed_end
    open_end = (
        hinge[0] + in_x * opening.width,
        hinge[1] + in_y * opening.width,
    )

    xs = [closed_start[0], closed_end[0], hinge[0], open_end[0]]
    ys = [closed_start[1], closed_end[1], hinge[1], open_end[1]]
    return (
        min(xs) - clearance,
        min(ys) - clearance,
        max(xs) + clearance,
        max(ys) + clearance,
    )


def window_footprint(
    room,
    opening: Opening,
    clearance: float,
    depth: float = 0.15,
) -> Rect:
    wall_start, wall_end = wall_points(room, opening.wall)
    dx = wall_end[0] - wall_start[0]
    dy = wall_end[1] - wall_start[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return (wall_start[0], wall_start[1], wall_start[0], wall_start[1])

    ux, uy = dx / length, dy / length
    in_x, in_y = -uy, ux
    p_start = (
        wall_start[0] + ux * opening.offset,
        wall_start[1] + uy * opening.offset,
    )
    p_end = (
        wall_start[0] + ux * (opening.offset + opening.width),
        wall_start[1] + uy * (opening.offset + opening.width),
    )
    xs = [p_start[0], p_end[0], p_start[0] + in_x * depth, p_end[0] + in_x * depth]
    ys = [p_start[1], p_end[1], p_start[1] + in_y * depth, p_end[1] + in_y * depth]
    return (
        min(xs) - clearance,
        min(ys) - clearance,
        max(xs) + clearance,
        max(ys) + clearance,
    )


def overlap_area(first: Rect, second: Rect) -> float:
    overlap_w = min(first[2], second[2]) - max(first[0], second[0])
    overlap_h = min(first[3], second[3]) - max(first[1], second[1])
    if overlap_w <= 0 or overlap_h <= 0:
        return 0.0
    return round(overlap_w * overlap_h, 10)
