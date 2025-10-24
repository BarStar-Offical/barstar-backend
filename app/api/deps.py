from __future__ import annotations

from collections.abc import Generator

from collections.abc import Generator

from app.core.config import get_settings
from app.db.session import get_db_session
from app.services.task_queue import TaskQueue

settings = get_settings()


def get_db() -> Generator:
    """FastAPI dependency that yields a synchronous SQLAlchemy session."""

    yield from get_db_session()


def get_task_queue() -> Generator[TaskQueue, None, None]:
    """Provide a task queue instance tied to the request lifecycle."""

    queue = TaskQueue(str(settings.redis_url))
    try:
        yield queue
    finally:
        queue.close()
