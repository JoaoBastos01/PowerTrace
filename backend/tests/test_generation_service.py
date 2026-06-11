import pytest

from app.config import settings
from app.schemas.generation import GenerationCreateRequest
from app.services.generation import (
    FloorPlanGenerationError,
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
