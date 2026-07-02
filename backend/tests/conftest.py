import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base, get_db
from app.main import app


TEST_SECRET = "test-secret-key-with-at-least-thirty-two-characters"


@pytest.fixture
def api(monkeypatch, tmp_path):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(settings, "secret_key", TEST_SECRET)
    monkeypatch.setattr(settings, "output_dir", str(tmp_path / "output"))
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    try:
        yield client, testing_session
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
