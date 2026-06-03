"""Database configuration for SQLAlchemy."""

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    
connect_args = {}

if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    
engine = create_engine(settings.database_url, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        
def init_db() -> None:
    import app.db_models # noqa:F401    
    Base.metadata.create_all(bind=engine)
    apply_sqlite_schema_updates()


def apply_sqlite_schema_updates() -> None:
    """Apply small SQLite updates until proper migrations are added."""
    if not settings.database_url.startswith("sqlite"):
        return

    inspector = inspect(engine)
    if "projects" not in inspector.get_table_names():
        return

    project_columns = {
        column["name"] for column in inspector.get_columns("projects")
    }
    if "description" not in project_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE projects ADD COLUMN description TEXT"))
