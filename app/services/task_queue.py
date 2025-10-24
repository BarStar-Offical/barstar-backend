from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import redis
import structlog

logger = structlog.get_logger(__name__)


class TaskQueue:
    """Minimal Redis-backed FIFO queue."""

    def __init__(self, url: str, namespace: str = "tasks"):
        self._client = redis.from_url(url, encoding="utf-8", decode_responses=True)
        self._namespace = namespace

    def enqueue(self, task: str, payload: dict[str, Any] | None = None) -> None:
        """Push a JSON payload onto the queue."""

        message = {
            "task": task,
            "payload": payload or {},
            "enqueued_at": datetime.now(timezone.utc).isoformat(),
        }
        self._client.lpush(self._namespace, json.dumps(message))
        logger.info("task_enqueued", task=task)

    def close(self) -> None:
        """Close the underlying Redis connection."""

        if self._client:
            self._client.close()
