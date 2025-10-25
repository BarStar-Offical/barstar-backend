from __future__ import annotations

from datetime import datetime, timezone
from typing import Generator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import deps
from app.db.base import Base
from app.main import create_app
from app.models import Users


@pytest.fixture()
def app_session() -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        future=True,
    )
    Base.metadata.create_all(bind=engine)

    app = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        with TestingSessionLocal() as session:
            yield session

    def override_get_task_queue() -> Generator[object, None, None]:
        class _Queue:
            def enqueue(self, *_args, **_kwargs) -> None:
                return None

            def close(self) -> None:
                return None

        yield _Queue()

    app.dependency_overrides[deps.get_db] = override_get_db
    app.dependency_overrides[deps.get_task_queue] = override_get_task_queue

    client = TestClient(app)

    try:
        yield client, TestingSessionLocal
    finally:
        client.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _create_user(session_factory: sessionmaker[Session]) -> UUID:
    with session_factory() as session:
        user = Users(email="test@example.com")
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def test_record_and_fetch_latest_location(
    app_session: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = app_session
    user_id = _create_user(session_factory)

    payload = {
        "latitude": 40.7128,
        "longitude": -74.006,
        "accuracy": 5.0,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }

    post_response = client.post(f"/api/v1/users/{user_id}/locations", json=payload)
    assert post_response.status_code == 201
    body = post_response.json()
    assert body["user_id"] == str(user_id)
    assert body["latitude"] == pytest.approx(payload["latitude"])
    assert body["longitude"] == pytest.approx(payload["longitude"])
    assert body["accuracy"] == pytest.approx(payload["accuracy"])

    get_response = client.get(f"/api/v1/users/{user_id}/locations/latest")
    assert get_response.status_code == 200
    latest = get_response.json()
    assert latest["id"] == body["id"]
    assert latest["captured_at"] == body["captured_at"]


def test_get_latest_location_returns_404_when_missing(
    app_session: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = app_session
    user_id = _create_user(session_factory)

    response = client.get(f"/api/v1/users/{user_id}/locations/latest")
    assert response.status_code == 404
    assert response.json()["detail"] == "location_not_found"
