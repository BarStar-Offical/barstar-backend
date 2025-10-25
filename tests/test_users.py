from __future__ import annotations

from collections.abc import Generator
from typing import Any
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
def api_app() -> Generator[
    tuple[TestClient, sessionmaker[Session], list[tuple[str, dict[str, Any]]]],
    None,
    None,
]:
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
    events: list[tuple[str, dict[str, Any]]] = []

    def override_get_db() -> Generator[Session, None, None]:
        with TestingSessionLocal() as session:
            yield session

    def override_get_task_queue() -> Generator[object, None, None]:
        class _Queue:
            def enqueue(self, name: str, payload: dict[str, Any]) -> None:
                events.append((name, payload))

            def close(self) -> None:
                return None

        yield _Queue()

    app.dependency_overrides[deps.get_db] = override_get_db
    app.dependency_overrides[deps.get_task_queue] = override_get_task_queue

    client = TestClient(app)

    try:
        yield client, TestingSessionLocal, events
    finally:
        client.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_create_user(api_app: tuple[TestClient, sessionmaker[Session], list[tuple[str, dict[str, Any]]]]) -> None:
    client, session_factory, events = api_app
    payload = {
        "email": "create@example.com",
        "full_name": "Create User",
        "oauth_provider": "github",
        "oauth_provider_id": "oauth-create",
    }

    response = client.post("/api/v1/users", json=payload)
    assert response.status_code == 201

    body = response.json()
    assert body["email"] == payload["email"]
    assert body["full_name"] == payload["full_name"]
    assert body["oauth_provider"] == payload["oauth_provider"]
    assert body["oauth_provider_id"] == payload["oauth_provider_id"]
    assert body["points"] == 0
    assert events == [("user.created", {"id": body["id"]})]

    with session_factory() as session:
        stored = session.get(Users, UUID(body["id"]))
        assert stored is not None
        assert stored.email == payload["email"]
        assert stored.full_name == payload["full_name"]


def test_create_user_conflict(api_app: tuple[TestClient, sessionmaker[Session], list[tuple[str, dict[str, Any]]]]) -> None:
    client, _session_factory, events = api_app
    payload = {
        "email": "duplicate@example.com",
        "full_name": "Original",
        "oauth_provider": "google",
        "oauth_provider_id": "oauth-dup-1",
    }

    first = client.post("/api/v1/users", json=payload)
    assert first.status_code == 201
    events.clear()

    conflicting_payload = dict(payload)
    conflicting_payload["oauth_provider_id"] = "oauth-dup-2"

    response = client.post("/api/v1/users", json=conflicting_payload)
    assert response.status_code == 409
    assert response.json()["detail"] == "user_already_exists"
    assert events == []


def test_update_user(api_app: tuple[TestClient, sessionmaker[Session], list[tuple[str, dict[str, Any]]]]) -> None:
    client, session_factory, events = api_app
    create_payload = {
        "email": "update@example.com",
        "full_name": "Before Update",
        "oauth_provider": "facebook",
        "oauth_provider_id": "oauth-update",
    }

    response = client.post("/api/v1/users", json=create_payload)
    assert response.status_code == 201
    user_id = response.json()["id"]

    events.clear()

    update_payload = {"full_name": "After Update", "points": 42}
    update_response = client.put(f"/api/v1/users/{user_id}", json=update_payload)
    assert update_response.status_code == 200

    body = update_response.json()
    assert body["full_name"] == "After Update"
    assert body["points"] == 42
    assert events == [("user.updated", {"id": user_id})]

    with session_factory() as session:
        stored = session.get(Users, UUID(user_id))
        assert stored is not None
        assert stored.full_name == "After Update"
        assert stored.points == 42


def test_delete_user(api_app: tuple[TestClient, sessionmaker[Session], list[tuple[str, dict[str, Any]]]]) -> None:
    client, session_factory, events = api_app
    payload = {
        "email": "delete@example.com",
        "full_name": "Delete Me",
        "oauth_provider": "apple",
        "oauth_provider_id": "oauth-delete",
    }

    response = client.post("/api/v1/users", json=payload)
    assert response.status_code == 201
    user_id = response.json()["id"]

    events.clear()

    delete_response = client.delete(f"/api/v1/users/{user_id}")
    assert delete_response.status_code == 204
    assert events == [("user.deleted", {"id": user_id})]

    with session_factory() as session:
        assert session.get(Users, UUID(user_id)) is None

    get_response = client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "user_not_found"
