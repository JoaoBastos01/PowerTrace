"""Add persistent users and relational ownership.

Revision ID: 20260610_01
Revises:
Create Date: 2026-06-10
"""

import os
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
from email_validator import EmailNotValidError, validate_email
from pwdlib import PasswordHash
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260610_01"
down_revision = None
branch_labels = None
depends_on = None


def _create_users_table() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def _bootstrap_user(connection) -> str | None:
    email = os.getenv("BOOTSTRAP_USER_EMAIL")
    name = os.getenv("BOOTSTRAP_USER_NAME")
    password = os.getenv("BOOTSTRAP_USER_PASSWORD")
    if not all((email, name, password)):
        return None

    if len(password) < 8 or len(password) > 128:
        raise RuntimeError(
            "BOOTSTRAP_USER_PASSWORD must contain between 8 and 128 characters."
        )
    try:
        normalized_email = validate_email(
            email, check_deliverability=False
        ).normalized.lower()
    except EmailNotValidError as exc:
        raise RuntimeError("BOOTSTRAP_USER_EMAIL is invalid.") from exc
    existing = connection.execute(
        sa.text("SELECT id FROM users WHERE email = :email"),
        {"email": normalized_email},
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    user_id = str(uuid4())
    now = datetime.now(timezone.utc)
    connection.execute(
        sa.text(
            """
            INSERT INTO users
                (id, email, name, password_hash, is_active, created_at, updated_at)
            VALUES
                (:id, :email, :name, :password_hash, :is_active, :created_at, :updated_at)
            """
        ),
        {
            "id": user_id,
            "email": normalized_email,
            "name": name.strip(),
            "password_hash": PasswordHash.recommended().hash(password),
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
    )
    return user_id


def _create_projects_table() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "owner_id",
            sa.String(36),
            sa.ForeignKey("users.id", name="fk_projects_owner_id_users"),
            nullable=False,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_projects_owner_id", "projects", ["owner_id"])


def _create_generations_table() -> None:
    op.create_table(
        "generations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id", name="fk_generations_project_id_projects"),
            nullable=False,
        ),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("input_json", sa.Text(), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("dxf_filename", sa.Text(), nullable=True),
        sa.Column("json_filename", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_generations_project_id", "generations", ["project_id"])


def upgrade() -> None:
    connection = op.get_bind()
    inspector = inspect(connection)
    tables = set(inspector.get_table_names())

    if "users" not in tables:
        _create_users_table()

    bootstrap_user_id = _bootstrap_user(connection)

    if "projects" not in tables:
        _create_projects_table()
    else:
        project_count = connection.execute(
            sa.text("SELECT COUNT(*) FROM projects")
        ).scalar_one()
        if project_count and bootstrap_user_id is None:
            raise RuntimeError(
                "BOOTSTRAP_USER_EMAIL, BOOTSTRAP_USER_NAME and "
                "BOOTSTRAP_USER_PASSWORD are required to migrate existing projects."
            )
        if project_count:
            legacy_username = os.getenv("APP_USERNAME")
            if legacy_username:
                connection.execute(
                    sa.text(
                        "UPDATE projects SET owner_id = :user_id "
                        "WHERE owner_id = :legacy_owner"
                    ),
                    {"user_id": bootstrap_user_id, "legacy_owner": legacy_username},
                )
            connection.execute(
                sa.text(
                    "UPDATE projects SET owner_id = :user_id "
                    "WHERE owner_id IS NULL OR owner_id NOT IN (SELECT id FROM users)"
                ),
                {"user_id": bootstrap_user_id},
            )
            connection.execute(
                sa.text(
                    "UPDATE projects SET name = 'Untitled project' "
                    "WHERE name IS NULL OR TRIM(name) = ''"
                )
            )

        with op.batch_alter_table("projects", recreate="always") as batch_op:
            batch_op.alter_column(
                "owner_id",
                existing_type=sa.Text(),
                type_=sa.String(36),
                nullable=False,
            )
            batch_op.alter_column(
                "name",
                existing_type=sa.Text(),
                type_=sa.String(120),
                nullable=False,
            )
            batch_op.create_foreign_key(
                "fk_projects_owner_id_users", "users", ["owner_id"], ["id"]
            )
            batch_op.create_index("ix_projects_owner_id", ["owner_id"])

    inspector = inspect(connection)
    if "generations" not in inspector.get_table_names():
        _create_generations_table()
    else:
        connection.execute(
            sa.text(
                "UPDATE generations SET status = 'pending' "
                "WHERE status IS NULL OR TRIM(status) = ''"
            )
        )
        orphan_count = connection.execute(
            sa.text(
                "SELECT COUNT(*) FROM generations "
                "WHERE project_id IS NULL OR project_id NOT IN (SELECT id FROM projects)"
            )
        ).scalar_one()
        if orphan_count:
            raise RuntimeError(
                "Cannot migrate generations that are not linked to an existing project."
            )
        with op.batch_alter_table("generations", recreate="always") as batch_op:
            batch_op.alter_column(
                "project_id",
                existing_type=sa.Text(),
                type_=sa.String(36),
                nullable=False,
            )
            batch_op.alter_column(
                "status",
                existing_type=sa.Text(),
                type_=sa.String(32),
                nullable=False,
            )
            batch_op.create_foreign_key(
                "fk_generations_project_id_projects",
                "projects",
                ["project_id"],
                ["id"],
            )
            batch_op.create_index("ix_generations_project_id", ["project_id"])


def downgrade() -> None:
    with op.batch_alter_table("generations", recreate="always") as batch_op:
        batch_op.drop_index("ix_generations_project_id")
        batch_op.drop_constraint(
            "fk_generations_project_id_projects", type_="foreignkey"
        )
        batch_op.alter_column(
            "project_id",
            existing_type=sa.String(36),
            type_=sa.Text(),
            nullable=True,
        )
        batch_op.alter_column(
            "status",
            existing_type=sa.String(32),
            type_=sa.Text(),
            nullable=True,
        )

    with op.batch_alter_table("projects", recreate="always") as batch_op:
        batch_op.drop_index("ix_projects_owner_id")
        batch_op.drop_constraint("fk_projects_owner_id_users", type_="foreignkey")
        batch_op.alter_column(
            "owner_id",
            existing_type=sa.String(36),
            type_=sa.Text(),
            nullable=True,
        )
        batch_op.alter_column(
            "name",
            existing_type=sa.String(120),
            type_=sa.Text(),
            nullable=True,
        )

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
