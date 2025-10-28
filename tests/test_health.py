from __future__ import annotations

from typing import Generator

from app.api import deps
from app.main import create_app
from fastapi.testclient import TestClient


def test_health_endpoint_returns_ok() -> None:
    app = create_app()
    app.dependency_overrides[deps.get_db] = _override_get_db

    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def _override_get_db() -> Generator[object, None, None]:
    class _Session:
        def execute(self, *_args, **_kwargs) -> None: # type: ignore
            return None

    yield _Session()
