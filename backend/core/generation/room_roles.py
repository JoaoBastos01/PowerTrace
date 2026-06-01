"""Architectural role and display-name resolution for generated rooms."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RoomPresentation:
    room_role: str
    display_name: str


DEFAULT_ROOM_ROLES = {
    "living": "living_area",
    "kitchen": "kitchen",
    "living_kitchen": "living_kitchen",
    "corridor": "circulation",
    "garage": "garage",
}


def default_display_name(room_type: str) -> str:
    return room_type.replace("_", " ").title()


def resolve_room_presentation(room_type: str, category: str) -> RoomPresentation:
    if room_type == "bathroom_1" and category in ("kitnet", "small"):
        return RoomPresentation(
            room_role="social_full_bathroom",
            display_name="Social Bathroom",
        )
    if room_type == "bathroom_social":
        return RoomPresentation(
            room_role="powder_room",
            display_name="Social WC",
        )
    if room_type.startswith("bathroom"):
        return RoomPresentation(
            room_role="full_bathroom",
            display_name=default_display_name(room_type),
        )
    if room_type.startswith("bedroom"):
        return RoomPresentation(
            room_role="bedroom",
            display_name=default_display_name(room_type),
        )
    return RoomPresentation(
        room_role=DEFAULT_ROOM_ROLES.get(room_type, "room"),
        display_name=default_display_name(room_type),
    )
