from app.schemas.generation import GeneratedRoomResult
from core.electrical.room_catalog import room_spec_to_base_room
from core.electrical.rooms import Bathroom, BathroomSocial
from core.generation.room_roles import resolve_room_presentation
from models.floor_plan import RoomSpec


def test_small_primary_bathroom_is_presented_as_social_full_bathroom():
    presentation = resolve_room_presentation("bathroom_1", "small")

    assert presentation.room_role == "social_full_bathroom"
    assert presentation.display_name == "Social Bathroom"


def test_bathroom_social_is_presented_as_powder_room():
    presentation = resolve_room_presentation("bathroom_social", "medium")

    assert presentation.room_role == "powder_room"
    assert presentation.display_name == "Social WC"


def test_primary_bathroom_still_uses_full_bathroom_electrical_model():
    room_spec = RoomSpec("bathroom_1", x=0.0, y=0.0, width=1.5, length=2.0)
    room = room_spec_to_base_room(room_spec, display_name="Social Bathroom")

    assert isinstance(room, Bathroom)
    assert not isinstance(room, BathroomSocial)
    assert room.name == "Social Bathroom"


def test_room_response_exposes_technical_type_role_and_display_name():
    response = GeneratedRoomResult(
        room_type="bathroom_1",
        room_role="social_full_bathroom",
        name="Social Bathroom",
        x=0.0,
        y=0.0,
        width=1.5,
        length=2.0,
        area=3.0,
        total_wattage=5636,
        exterior_walls=["S"],
    )

    assert response.room_type == "bathroom_1"
    assert response.room_role == "social_full_bathroom"
    assert response.name == "Social Bathroom"
