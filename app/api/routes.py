from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_task_queue
from app.models import User
from app.schemas import UserCreate, UserRead
from app.services import TaskQueue

router = APIRouter(prefix="/api/v1")


@router.get("/health", tags=["health"])
def healthcheck(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Readiness probe that verifies database connectivity."""

    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - defensive branch
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database_unavailable",
        ) from exc
    return {"status": "ok"}


@router.post(
    "/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    tags=["users"],
)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    queue: TaskQueue = Depends(get_task_queue),
) -> UserRead:
    """Create a new user and enqueue a lightweight background event."""

    existing_user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="user_already_exists",
        )

    user = User(email=payload.email, full_name=payload.full_name)
    db.add(user)
    db.commit()
    db.refresh(user)

    queue.enqueue("user.created", {"id": str(user.id)})
    return UserRead.model_validate(user)


@router.get(
    "/users",
    response_model=list[UserRead],
    tags=["users"],
)
def list_users(db: Session = Depends(get_db)) -> list[UserRead]:
    """List all users ordered by creation date."""

    result = db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [UserRead.model_validate(user) for user in users]
