import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config


def test_legacy_project_owner_is_migrated_to_bootstrap_user(tmp_path, monkeypatch):
    database_path = tmp_path / "legacy.db"
    connection = sqlite3.connect(database_path)
    connection.executescript(
        """
        CREATE TABLE projects (
            id VARCHAR(36) PRIMARY KEY NOT NULL,
            owner_id TEXT,
            name TEXT,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            description TEXT
        );
        CREATE TABLE generations (
            id VARCHAR(36) PRIMARY KEY NOT NULL,
            project_id TEXT,
            status TEXT,
            input_json TEXT,
            result_json TEXT,
            dxf_filename TEXT,
            json_filename TEXT,
            error_message TEXT,
            created_at DATETIME NOT NULL
        );
        INSERT INTO projects
            (id, owner_id, name, created_at, updated_at, description)
        VALUES
            ('project-1', 'legacy-admin', 'Legacy', CURRENT_TIMESTAMP,
             CURRENT_TIMESTAMP, NULL);
        """
    )
    connection.commit()
    connection.close()

    monkeypatch.setenv("APP_USERNAME", "legacy-admin")
    monkeypatch.setenv("BOOTSTRAP_USER_EMAIL", "admin@example.com")
    monkeypatch.setenv("BOOTSTRAP_USER_NAME", "Administrator")
    monkeypatch.setenv("BOOTSTRAP_USER_PASSWORD", "strongpass123")

    backend_root = Path(__file__).resolve().parents[1]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path.as_posix()}")
    command.upgrade(config, "head")

    connection = sqlite3.connect(database_path)
    user = connection.execute(
        "SELECT id, email, password_hash FROM users"
    ).fetchone()
    project_owner = connection.execute(
        "SELECT owner_id FROM projects WHERE id = 'project-1'"
    ).fetchone()[0]
    project_foreign_keys = connection.execute(
        "PRAGMA foreign_key_list(projects)"
    ).fetchall()
    generation_foreign_keys = connection.execute(
        "PRAGMA foreign_key_list(generations)"
    ).fetchall()
    connection.close()

    assert user[1] == "admin@example.com"
    assert user[2].startswith("$argon2")
    assert project_owner == user[0]
    assert any(row[2] == "users" for row in project_foreign_keys)
    assert any(row[2] == "projects" for row in generation_foreign_keys)
