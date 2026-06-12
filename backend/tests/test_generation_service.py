import pytest

from app.config import settings
from app.schemas.generation import GenerationCreateRequest
from app.services.generation import (
    FloorPlanGenerationError,
    GenerationInputError,
    generate_project_artifact,
)


def test_generation_service_creates_unique_deterministic_dxf(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "output_dir", str(tmp_path))
    monkeypatch.setattr(settings, "max_generation_attempts", 300)
    request = GenerationCreateRequest(width=8, length=12, seed=42)

    first = generate_project_artifact(request, "first-id")
    second = generate_project_artifact(request, "second-id")

    first_path = tmp_path / "generation_first-id.dxf"
    second_path = tmp_path / "generation_second-id.dxf"
    assert first_path.is_file()
    assert second_path.is_file()
    assert first.dxf_filename == first_path.name
    assert second.dxf_filename == second_path.name
    assert first.seed == 42
    assert first.total_power_w == sum(
        room.total_wattage for room in first.rooms
    )
    assert first.circuits
    assert first.circuits[0].id == "C01"
    assert all(
        circuit.breaker_a >= circuit.design_current_a
        for circuit in first.circuits
    )
    assert all(
        circuit.wire_max_current_a >= circuit.breaker_a
        for circuit in first.circuits
    )
    assert first.model_dump(exclude={"dxf_filename"}) == second.model_dump(
        exclude={"dxf_filename"}
    )
    assert first_path.read_bytes() == second_path.read_bytes()


def test_generation_service_propagates_known_failure_and_removes_partial_file(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "output_dir", str(tmp_path))
    partial_path = tmp_path / "generation_failed-id.dxf"

    def fail_generation(self, max_attempts):
        partial_path.write_bytes(b"partial")
        raise ValueError("No valid layout.")

    monkeypatch.setattr(
        "app.services.generation.FloorPlanGenerator.generate",
        fail_generation,
    )

    with pytest.raises(FloorPlanGenerationError, match="No valid layout"):
        generate_project_artifact(
            GenerationCreateRequest(width=8, length=12, seed=7),
            "failed-id",
        )

    assert not partial_path.exists()


def test_generation_service_applies_tue_overrides_to_result_and_dxf(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "output_dir", str(tmp_path))
    monkeypatch.setattr(settings, "max_generation_attempts", 300)

    baseline = generate_project_artifact(
        GenerationCreateRequest(width=8, length=12, seed=42),
        "baseline-id",
    )
    overridden = generate_project_artifact(
        GenerationCreateRequest(
            width=8,
            length=12,
            seed=42,
            rooms=[
                {
                    "room_key": "kitchen",
                    "room_type": "kitchen",
                    "display_name": "Custom Kitchen",
                    "specific_outlets": [
                        {
                            "id": "kitchen_electric_faucet",
                            "enabled": False,
                            "source": "default",
                        },
                        {
                            "id": "custom_oven",
                            "name": "Electric oven",
                            "power_w": 3000,
                            "voltage": 220,
                            "source": "custom",
                        },
                        {
                            "id": "custom_air_conditioner",
                            "name": "Air conditioner",
                            "quantity": 2,
                            "power_w": 1500,
                            "voltage": 220,
                            "power_factor": 0.92,
                            "source": "custom",
                        },
                    ],
                }
            ],
        ),
        "overridden-id",
    )

    baseline_kitchen = next(
        room for room in baseline.rooms if room.room_type == "kitchen"
    )
    overridden_kitchen = next(
        room for room in overridden.rooms if room.room_type == "kitchen"
    )
    outlet_keys = {
        outlet.key for outlet in overridden_kitchen.specific_outlets
    }

    assert overridden_kitchen.name == "Custom Kitchen"
    assert "kitchen_electric_faucet" not in outlet_keys
    assert "custom_oven" in outlet_keys
    assert "custom_air_conditioner_1" in outlet_keys
    assert "custom_air_conditioner_2" in outlet_keys
    assert overridden_kitchen.total_wattage == (
        baseline_kitchen.total_wattage - 5500 + 3000 + (2 * 1500)
    )
    oven = next(
        outlet
        for outlet in overridden_kitchen.specific_outlets
        if outlet.key == "custom_oven"
    )
    assert oven.power_w == 3000
    assert oven.voltage == 220
    assert oven.source == "custom"
    assert (tmp_path / "generation_overridden-id.dxf").is_file()

    custom_circuits = [
        circuit
        for circuit in overridden.circuits
        if any(
            point.key.startswith("custom_")
            for point in circuit.load_points
        )
    ]
    assert {circuit.total_power_w for circuit in custom_circuits} == {
        1500,
        3000,
    }
    assert all(circuit.voltage == 220 for circuit in custom_circuits)


def test_generation_service_rejects_load_above_dimensioning_tables(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "output_dir", str(tmp_path))
    request = GenerationCreateRequest(
        width=8,
        length=12,
        seed=42,
        rooms=[
            {
                "room_key": "kitchen",
                "room_type": "kitchen",
                "specific_outlets": [
                    {
                        "id": "industrial_oven",
                        "name": "Forno industrial",
                        "power_w": 100000,
                        "voltage": 127,
                        "source": "custom",
                    }
                ],
            }
        ],
    )

    with pytest.raises(GenerationInputError, match="dimensionar"):
        generate_project_artifact(request, "oversized-load-id")

    assert not (tmp_path / "generation_oversized-load-id.dxf").exists()


def test_generation_service_rejects_override_for_room_not_generated(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "output_dir", str(tmp_path))
    monkeypatch.setattr(settings, "max_generation_attempts", 300)
    request = GenerationCreateRequest(
        width=8,
        length=12,
        seed=42,
        rooms=[
            {
                "room_key": "attic",
                "room_type": "attic",
                "specific_outlets": [],
            }
        ],
    )

    with pytest.raises(GenerationInputError, match="attic"):
        generate_project_artifact(request, "unknown-room-id")

    assert not (tmp_path / "generation_unknown-room-id.dxf").exists()
