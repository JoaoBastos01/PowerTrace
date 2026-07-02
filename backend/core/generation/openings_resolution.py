"""Candidate selection for door and window openings."""

import math
from typing import List, Tuple

from core.drawing.openings import Opening
from core.generation.openings_geometry import (
    Rect,
    door_footprint,
    overlap_area,
    wall_length,
    window_footprint,
)


def offset_candidates(
    preferred: float,
    minimum: float,
    maximum: float,
    candidate_step: float,
) -> List[float]:
    if maximum < minimum:
        return []

    preferred = max(minimum, min(preferred, maximum))
    candidates = []
    seen = set()

    def add(value: float) -> None:
        value = max(minimum, min(value, maximum))
        key = round(value, 8)
        if key not in seen:
            seen.add(key)
            candidates.append(key)

    add(preferred)
    span = max(abs(preferred - minimum), abs(maximum - preferred))
    steps = int(math.ceil(span / candidate_step))
    for step in range(1, steps + 1):
        delta = candidate_step * step
        add(preferred - delta)
        add(preferred + delta)
    add(minimum)
    add(maximum)
    return candidates


def swing_candidates(preferred: str) -> List[str]:
    opposite = 'left' if preferred == 'right' else 'right'
    return [preferred, opposite]


def resolve_door_opening(
    room,
    wall: str,
    preferred_offset: float,
    width: float,
    preferred_swing: str,
    occupied_footprints: List[Rect],
    minimum_offset: float,
    maximum_offset: float,
    candidate_step: float,
    clearance: float,
) -> Tuple[Opening, Rect]:
    candidates = offset_candidates(
        preferred_offset,
        minimum_offset,
        maximum_offset,
        candidate_step,
    )
    if not candidates:
        fallback = Opening(wall=wall, offset=preferred_offset, width=width, kind='door', swing=preferred_swing)
        return fallback, door_footprint(room, fallback, clearance)

    best_score = None
    best_opening = None
    best_footprint = None
    for offset_index, offset in enumerate(candidates):
        for swing_index, swing in enumerate(swing_candidates(preferred_swing)):
            opening = Opening(wall=wall, offset=offset, width=width, kind='door', swing=swing)
            footprint = door_footprint(room, opening, clearance)
            overlap_areas = [
                overlap_area(footprint, occupied)
                for occupied in occupied_footprints
            ]
            collision_count = sum(1 for area in overlap_areas if area > 0)
            total_overlap = round(sum(overlap_areas), 10)
            score = (
                collision_count,
                total_overlap,
                swing_index,
                round(abs(offset - preferred_offset), 8),
                offset_index,
                round(offset, 8),
            )
            if best_score is None or score < best_score:
                best_score = score
                best_opening = opening
                best_footprint = footprint

    return best_opening, best_footprint


def resolve_window_opening(
    room,
    wall: str,
    preferred_offset: float,
    width: float,
    occupied_footprints: List[Rect],
    minimum_offset: float,
    maximum_offset: float,
    candidate_step: float,
    clearance: float,
    min_width: float,
) -> Opening | None:
    if maximum_offset < minimum_offset or width < min_width:
        return None

    best_score = None
    best_opening = None
    for offset_index, offset in enumerate(
        offset_candidates(preferred_offset, minimum_offset, maximum_offset, candidate_step)
    ):
        opening = Opening(wall=wall, offset=offset, width=width, kind='window')
        footprint = window_footprint(room, opening, clearance)
        overlap_areas = [
            overlap_area(footprint, occupied)
            for occupied in occupied_footprints
        ]
        collision_count = sum(1 for area in overlap_areas if area > 0)
        total_overlap = round(sum(overlap_areas), 10)
        score = (
            collision_count,
            total_overlap,
            round(abs(offset - preferred_offset), 8),
            offset_index,
            round(offset, 8),
        )
        if best_score is None or score < best_score:
            best_score = score
            best_opening = opening

    if best_score and best_score[0] == 0:
        return best_opening
    return None


def resolve_exterior_window(
    room,
    wall: str,
    preferred_offset: float,
    preferred_width: float,
    occupied_footprints: List[Rect],
    min_margin: float,
    candidate_step: float,
    clearance: float,
    min_width: float,
) -> Opening | None:
    width = min(preferred_width, wall_length(room, wall) - 2 * min_margin)
    while width >= min_width:
        maximum_offset = wall_length(room, wall) - width - min_margin
        opening = resolve_window_opening(
            room,
            wall,
            preferred_offset,
            width,
            occupied_footprints,
            min_margin,
            maximum_offset,
            candidate_step,
            clearance,
            min_width,
        )
        if opening:
            return opening
        width = round(width - 0.20, 8)
    return None
