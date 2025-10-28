from __future__ import annotations

import os
import uuid
from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.api import deps
from app.db.base import Base
from app.main import create_app

APITestContext = tuple[TestClient, sessionmaker[Session], list[tuple[str, dict[str, Any]]]]


@pytest.fixture(scope="session")
def test_database_url() -> Generator[str, None, None]:
    raw_url = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/barstar_test",
    )
    url = make_url(raw_url)
    base_name = url.database or "barstar_test"
    database_name = f"{base_name}_{uuid.uuid4().hex[:8]}"

    admin_url = url.set(database="postgres")
    admin_engine = create_engine(admin_url, future=True, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
        connection.execute(text(f'CREATE DATABASE "{database_name}" TEMPLATE template0'))
    admin_engine.dispose()

    test_url = url.set(database=database_name)
    test_engine = create_engine(test_url, future=True, isolation_level="AUTOCOMMIT")
    with test_engine.connect() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
    test_engine.dispose()

    try:
        yield test_url.render_as_string(hide_password=False)
    finally:
        admin_engine = create_engine(admin_url, future=True, isolation_level="AUTOCOMMIT")
        with admin_engine.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) "
                    "FROM pg_stat_activity "
                    "WHERE datname = :db_name AND pid <> pg_backend_pid()"
                ),
                {"db_name": database_name},
            )
            connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
        admin_engine.dispose()


@pytest.fixture()
def api_app(test_database_url: str) -> Generator[APITestContext, None, None]:
    engine = create_engine(
        test_database_url,
        future=True,
        poolclass=NullPool,
        pool_pre_ping=True,
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
        engine.dispose()
