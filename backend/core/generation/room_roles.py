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

DEFAULT_DISPLAY_NAMES = {
    "living": "Sala",
    "kitchen": "Cozinha",
    "living_kitchen": "Sala e cozinha",
    "corridor": "Corredor",
    "garage": "Garagem",
}


def default_display_name(room_type: str) -> str:
    if room_type in DEFAULT_DISPLAY_NAMES:
        return DEFAULT_DISPLAY_NAMES[room_type]
    if room_type.startswith("bedroom_"):
        return f"Quarto {room_type.removeprefix('bedroom_')}"
    if room_type.startswith("bathroom_"):
        return f"Banheiro {room_type.removeprefix('bathroom_')}"
    return room_type.replace("_", " ").title()


def resolve_room_presentation(room_type: str, category: str) -> RoomPresentation:
    if room_type == "bathroom_1":
        return RoomPresentation(
            room_role="social_full_bathroom",
            display_name="Banheiro social",
        )
    if room_type == "bathroom_social":
        return RoomPresentation(
            room_role="powder_room",
            display_name="Lavabo",
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
