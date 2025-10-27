from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest
from app.api import deps
from app.db.base import Base
from app.main import create_app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

APITestContext = tuple[TestClient, sessionmaker[Session], list[tuple[str, dict[str, Any]]]]


@pytest.fixture()
def api_app() -> Generator[APITestContext, None, None]:
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
