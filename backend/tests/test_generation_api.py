from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.config import settings
from app.db_models import Generation
from app.repositories.projects import ProjectRepository
from app.schemas.generation import (
    GeneratedRoomResult,
    GeneratedSpecificOutletResult,
    GenerationCreateRequest,
    GenerationResult,
)
from app.services.generation import FloorPlanGenerationError, GenerationInputError


def register_and_authorize(
    client: TestClient,
    email: str = "generator@example.com",
) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "name": "Generator", "password": "strongpass123"},
    )
    token = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "strongpass123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_project(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/projects",
        headers=headers,
        json={"name": "Generated house"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def fake_result(generation_id: str, seed: int) -> GenerationResult:
    return GenerationResult(
        seed=seed,
        category="medium",
        total_width=8,
        total_length=12,
        total_area=96,
        rooms=[
            GeneratedRoomResult(
                room_type="living",
                room_role="living",
                name="Living Room",
                x=0,
                y=0,
                width=4,
                length=4,
                area=16,
                total_wattage=300,
                exterior_walls=["S"],
            )
        ],
        dxf_filename=f"generation_{generation_id}.dxf",
    )


def test_generation_success_persists_seed_result_and_downloads(
    api, monkeypatch
):
    client, session_factory = api
    headers = register_and_authorize(client)
    project_id = create_project(client, headers)
    monkeypatch.setattr(
        "app.api.v1.routes.projects.secrets.randbits",
        lambda bits: 123456,
    )

    def generate(request, generation_id):
        assert request.seed == 123456
        result = fake_result(generation_id, request.seed)
        output = Path(settings.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        (output / result.dxf_filename).write_bytes(b"DXF test content")
        return result

    monkeypatch.setattr(
        "app.api.v1.routes.projects.generation_service.generate_project_artifact",
        generate,
    )

    response = client.post(
        f"/api/v1/projects/{project_id}/generations",
        headers=headers,
        json={"width": 8, "length": 12, "rooms": []},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "generated"
    assert body["seed"] == 123456
    assert body["error_message"] is None

    with session_factory() as db:
        generation = db.get(Generation, body["generation_id"])
        persisted_input = GenerationCreateRequest.model_validate_json(
            generation.input_json
        )
        persisted_result = GenerationResult.model_validate_json(
            generation.result_json
        )
        assert generation.status == "generated"
        assert persisted_input.seed == 123456
        assert persisted_result.seed == 123456

    detail = client.get(
        f"/api/v1/projects/{project_id}/generations/{body['generation_id']}",
        headers=headers,
    )
    assert detail.status_code == 200
    assert detail.json()["result"]["category"] == "medium"
    assert detail.json()["seed"] == 123456
    assert detail.json()["input"]["width"] == 8
    assert detail.json()["input"]["length"] == 12

    download = client.get(body["download_url"], headers=headers)
    assert download.status_code == 200
    assert download.content == b"DXF test content"
    assert download.headers["content-type"] == "application/dxf"
    assert "attachment" in download.headers["content-disposition"]


def test_known_generation_failure_returns_422_and_persists_failed(api, monkeypatch):
    client, session_factory = api
    headers = register_and_authorize(client)
    project_id = create_project(client, headers)

    def fail(request, generation_id):
        raise FloorPlanGenerationError("No valid layout.")

    monkeypatch.setattr(
        "app.api.v1.routes.projects.generation_service.generate_project_artifact",
        fail,
    )

    response = client.post(
        f"/api/v1/projects/{project_id}/generations",
        headers=headers,
        json={"width": 8, "length": 12, "seed": 7},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "failed"
    assert body["seed"] == 7
    assert body["error_message"] == "No valid layout."
    with session_factory() as db:
        generation = db.get(Generation, body["generation_id"])
        assert generation.status == "failed"
        assert generation.dxf_filename is None
        assert generation.result_json is None


def test_unexpected_generation_failure_returns_safe_500(api, monkeypatch):
    client, session_factory = api
    headers = register_and_authorize(client)
    project_id = create_project(client, headers)

    def fail(request, generation_id):
        raise RuntimeError("database password should not leak")

    monkeypatch.setattr(
        "app.api.v1.routes.projects.generation_service.generate_project_artifact",
        fail,
    )

    response = client.post(
        f"/api/v1/projects/{project_id}/generations",
        headers=headers,
        json={"width": 8, "length": 12, "seed": 8},
    )

    assert response.status_code == 500
    assert "database password" not in response.text
    body = response.json()
    with session_factory() as db:
        generation = db.get(Generation, body["generation_id"])
        assert generation.status == "failed"
        assert "database password" not in generation.error_message


def test_room_overrides_are_persisted_and_exposed_in_generation_detail(
    api, monkeypatch
):
    client, session_factory = api
    headers = register_and_authorize(client)
    project_id = create_project(client, headers)

    def generate(request, generation_id):
        room_input = request.rooms[0]
        assert room_input.room_key == "kitchen"
        assert room_input.specific_outlets[1].power_w == 3000
        return GenerationResult(
            seed=request.seed,
            category="medium",
            total_width=8,
            total_length=12,
            total_area=96,
            rooms=[
                GeneratedRoomResult(
                    room_type="kitchen",
                    room_role="kitchen",
                    name="Kitchen",
                    x=0,
                    y=0,
                    width=4,
                    length=4,
                    area=16,
                    total_wattage=4800,
                    exterior_walls=["S"],
                    specific_outlets=[
                        GeneratedSpecificOutletResult(
                            key="custom_oven",
                            name="Electric oven",
                            power_w=3000,
                            voltage=220,
                            power_factor=1.0,
                            source="custom",
                        )
                    ],
                )
            ],
            dxf_filename=f"generation_{generation_id}.dxf",
        )

    monkeypatch.setattr(
        "app.api.v1.routes.projects.generation_service.generate_project_artifact",
        generate,
    )

    payload = {
        "width": 8,
        "length": 12,
        "seed": 42,
        "rooms": [
            {
                "room_key": "kitchen",
                "room_type": "kitchen",
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
                ],
            }
        ],
    }
    response = client.post(
        f"/api/v1/projects/{project_id}/generations",
        headers=headers,
        json=payload,
    )

    assert response.status_code == 201
    body = response.json()
    with session_factory() as db:
        assert db.scalar(select(func.count()).select_from(Generation)) == 1
        generation = db.get(Generation, body["generation_id"])
        persisted_input = GenerationCreateRequest.model_validate_json(
            generation.input_json
        )
        assert persisted_input.rooms[0].specific_outlets[1].power_w == 3000

    detail = client.get(
        f"/api/v1/projects/{project_id}/generations/{body['generation_id']}",
        headers=headers,
    )
    assert detail.status_code == 200
    outlets = detail.json()["result"]["rooms"][0]["specific_outlets"]
    assert [outlet["key"] for outlet in outlets] == ["custom_oven"]
    assert outlets[0]["power_w"] == 3000


def test_invalid_generation_override_returns_422_and_persists_failed(
    api, monkeypatch
):
    client, session_factory = api
    headers = register_and_authorize(client)
    project_id = create_project(client, headers)

    def fail(request, generation_id):
        raise GenerationInputError(
            "Room overrides reference rooms not present in the generated plan: attic."
        )

    monkeypatch.setattr(
        "app.api.v1.routes.projects.generation_service.generate_project_artifact",
        fail,
    )

    response = client.post(
        f"/api/v1/projects/{project_id}/generations",
        headers=headers,
        json={
            "width": 8,
            "length": 12,
            "seed": 42,
            "rooms": [
                {
                    "room_key": "attic",
                    "room_type": "attic",
                    "specific_outlets": [],
                }
            ],
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "failed"
    assert "attic" in body["error_message"]
    with session_factory() as db:
        generation = db.get(Generation, body["generation_id"])
        assert generation.status == "failed"


def test_generation_of_another_user_is_hidden(api, monkeypatch):
    client, _ = api
    headers_a = register_and_authorize(client, "a@example.com")
    headers_b = register_and_authorize(client, "b@example.com")
    project_id = create_project(client, headers_a)

    called = False

    def should_not_generate(request, generation_id):
        nonlocal called
        called = True
        return fake_result(generation_id, request.seed)

    monkeypatch.setattr(
        "app.api.v1.routes.projects.generation_service.generate_project_artifact",
        should_not_generate,
    )

    response = client.post(
        f"/api/v1/projects/{project_id}/generations",
        headers=headers_b,
        json={"width": 8, "length": 12, "seed": 9},
    )
    assert response.status_code == 404
    assert called is False


def test_download_returns_conflict_until_generated(api):
    client, session_factory = api
    headers = register_and_authorize(client)
    user = client.get("/api/v1/auth/me", headers=headers).json()
    project_id = create_project(client, headers)

    with session_factory() as db:
        repo = ProjectRepository(db)
        pending = repo.create_generation(
            user["id"],
            project_id,
            GenerationCreateRequest(width=8, length=12, seed=10),
        )
        failed = repo.create_generation(
            user["id"],
            project_id,
            GenerationCreateRequest(width=8, length=12, seed=11),
        )
        repo.mark_generation_failed(
            user["id"], project_id, failed.id, "Known failure."
        )
        pending_id = pending.id
        failed_id = failed.id

    for generation_id in (pending_id, failed_id):
        response = client.get(
            f"/api/v1/projects/{project_id}/generations/{generation_id}/download",
            headers=headers,
        )
        assert response.status_code == 409


def test_generated_metadata_with_missing_file_returns_404(api):
    client, session_factory = api
    headers = register_and_authorize(client)
    user = client.get("/api/v1/auth/me", headers=headers).json()
    project_id = create_project(client, headers)

    with session_factory() as db:
        repo = ProjectRepository(db)
        generation = repo.create_generation(
            user["id"],
            project_id,
            GenerationCreateRequest(width=8, length=12, seed=12),
        )
        repo.mark_generation_generated(
            user["id"],
            project_id,
            generation.id,
            fake_result(generation.id, 12),
        )
        generation_id = generation.id

    response = client.get(
        f"/api/v1/projects/{project_id}/generations/{generation_id}/download",
        headers=headers,
    )
    assert response.status_code == 404


def test_legacy_floor_plan_route_is_removed(api):
    client, _ = api
    response = client.post(
        "/api/v1/floor-plan/generate",
        json={"width": 8, "length": 12, "seed": 42},
    )
    assert response.status_code == 404


def test_cors_preflight_allows_local_vite_origin(api):
    client, _ = api

    response = client.options(
        "/api/v1/projects",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:5173"
    )
