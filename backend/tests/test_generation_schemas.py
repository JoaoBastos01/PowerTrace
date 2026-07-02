import pytest
from pydantic import ValidationError

from app.schemas.generation import GenerationCreateRequest, GenerationResult


def test_custom_tue_requires_power():
    with pytest.raises(ValidationError):
        GenerationCreateRequest(
            width=8,
            length=12,
            rooms=[{
                "room_key": "kitchen",
                "room_type": "kitchen",
                "specific_outlets": [{
                    "id": "custom_oven",
                    "name": "Forno",
                    "source": "custom",
                    "enabled": True,
                }],
            }],
        )


def test_default_tue_can_be_disabled_without_power():
    request = GenerationCreateRequest(
        width=8,
        length=12,
        rooms=[{
            "room_key": "kitchen",
            "room_type": "kitchen",
            "specific_outlets": [{
                "id": "kitchen_electric_faucet",
                "source": "default",
                "enabled": False,
            }],
        }],
    )

    assert request.rooms[0].specific_outlets[0].power_w is None


def test_custom_tue_preserves_electrical_configuration():
    request = GenerationCreateRequest(
        width=8,
        length=12,
        rooms=[
            {
                "room_key": "kitchen",
                "room_type": "kitchen",
                "specific_outlets": [
                    {
                        "id": "custom_oven",
                        "name": "Electric oven",
                        "power_w": 3000,
                        "voltage": 220,
                        "power_factor": 0.95,
                        "source": "custom",
                    }
                ],
            }
        ],
    )

    outlet = request.rooms[0].specific_outlets[0]
    assert outlet.power_w == 3000
    assert outlet.voltage == 220
    assert outlet.power_factor == 0.95


def test_legacy_generation_result_defaults_new_electrical_fields():
    result = GenerationResult.model_validate(
        {
            "seed": 42,
            "category": "medium",
            "total_width": 8,
            "total_length": 12,
            "total_area": 96,
            "rooms": [
                {
                    "room_type": "living",
                    "room_role": "living_area",
                    "name": "Sala",
                    "x": 0,
                    "y": 0,
                    "width": 4,
                    "length": 4,
                    "area": 16,
                    "total_wattage": 300,
                    "exterior_walls": ["S"],
                }
            ],
            "dxf_filename": "legacy.dxf",
        }
    )

    assert result.total_power_w == 0
    assert result.circuits == []
    assert result.rooms[0].load_points == []
    assert result.rooms[0].load_summary.total_power_w == 0
