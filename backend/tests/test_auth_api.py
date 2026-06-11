from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db_models import User
from app.repositories.projects import ProjectRepository
from app.schemas.generation import GenerationCreateRequest


TEST_SECRET = "test-secret-key-with-at-least-thirty-two-characters"


def register(client: TestClient, email: str, name: str = "Test User"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "name": name, "password": "strongpass123"},
    )


def login(client: TestClient, email: str, password: str = "strongpass123"):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def auth_headers(client: TestClient, email: str) -> dict[str, str]:
    token = login(client, email).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_normalizes_email_and_never_exposes_password(api):
    client, session_factory = api

    response = register(client, "  USER@Example.COM  ", "  User Name  ")

    assert response.status_code == 201
    assert response.json() == {
        "id": response.json()["id"],
        "email": "user@example.com",
        "name": "User Name",
    }
    assert "password" not in response.text

    with session_factory() as db:
        user = db.scalar(select(User).where(User.email == "user@example.com"))
        assert user is not None
        assert user.password_hash != "strongpass123"
        assert user.password_hash.startswith("$argon2")


def test_register_rejects_duplicate_and_invalid_payloads(api):
    client, _ = api
    assert register(client, "user@example.com").status_code == 201
    assert register(client, "USER@example.com").status_code == 409

    invalid_email = register(client, "not-an-email")
    short_password = client.post(
        "/api/v1/auth/register",
        json={"email": "other@example.com", "name": "Other", "password": "short"},
    )
    blank_name = client.post(
        "/api/v1/auth/register",
        json={
            "email": "other@example.com",
            "name": "   ",
            "password": "strongpass123",
        },
    )
    assert invalid_email.status_code == 422
    assert short_password.status_code == 422
    assert blank_name.status_code == 422


def test_login_and_me(api):
    client, _ = api
    user = register(client, "user@example.com").json()

    login_response = login(client, "USER@example.com")
    assert login_response.status_code == 200
    assert login_response.json()["token_type"] == "bearer"

    token = login_response.json()["access_token"]
    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    assert me.json() == user


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("missing@example.com", "strongpass123"),
        ("user@example.com", "wrongpass123"),
    ],
)
def test_login_rejects_invalid_credentials_with_generic_401(api, email, password):
    client, _ = api
    register(client, "user@example.com")

    response = login(client, email, password)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["detail"] == "Invalid or expired authentication credentials."


def test_protected_routes_require_bearer_token(api):
    client, _ = api

    projects = client.get("/api/v1/projects")

    assert projects.status_code == 401
    assert projects.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("token_kind", ["expired", "tampered", "missing_sub"])
def test_me_rejects_invalid_tokens(api, token_kind):
    client, _ = api
    register(client, "user@example.com")
    user_id = login(client, "user@example.com").json()["access_token"]
    valid_payload = jwt.decode(user_id, TEST_SECRET, algorithms=["HS256"])

    if token_kind == "expired":
        token = jwt.encode(
            {
                "sub": valid_payload["sub"],
                "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
            },
            TEST_SECRET,
            algorithm="HS256",
        )
    elif token_kind == "missing_sub":
        token = jwt.encode(
            {"exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
            TEST_SECRET,
            algorithm="HS256",
        )
    else:
        token = user_id + "tampered"

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("user_state", ["inactive", "deleted"])
def test_me_rejects_inactive_or_deleted_user(api, user_state):
    client, session_factory = api
    register(client, "user@example.com")
    token = login(client, "user@example.com").json()["access_token"]
    payload = jwt.decode(token, TEST_SECRET, algorithms=["HS256"])

    with session_factory() as db:
        user = db.get(User, payload["sub"])
        if user_state == "inactive":
            user.is_active = False
        else:
            db.delete(user)
        db.commit()

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_users_cannot_access_each_others_projects_or_generations(api):
    client, session_factory = api
    user_a = register(client, "a@example.com", "User A").json()
    register(client, "b@example.com", "User B")
    headers_a = auth_headers(client, "a@example.com")
    headers_b = auth_headers(client, "b@example.com")

    project_response = client.post(
        "/api/v1/projects",
        headers=headers_a,
        json={"name": "Private project", "description": "A only"},
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    assert client.get(
        f"/api/v1/projects/{project_id}", headers=headers_b
    ).status_code == 404

    with session_factory() as db:
        generation = ProjectRepository(db).create_generation(
            user_a["id"],
            project_id,
            GenerationCreateRequest(width=8, length=12, seed=42),
        )
        generation_id = generation.id

    assert client.get(
        f"/api/v1/projects/{project_id}/generations/{generation_id}",
        headers=headers_a,
    ).status_code == 200
    assert client.get(
        f"/api/v1/projects/{project_id}/generations/{generation_id}",
        headers=headers_b,
    ).status_code == 404
    assert client.get(
        f"/api/v1/projects/{project_id}/generations/{generation_id}/download",
        headers=headers_b,
    ).status_code == 404
