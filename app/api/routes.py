from __future__ import annotations

from datetime import timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_task_queue
from app.models import User, UserLocation
from app.schemas import (
    UserCreate,
    UserLocationCreate,
    UserLocationRead,
    UserRead,
)
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


@router.post(
    "/users/{user_id}/locations",
    response_model=UserLocationRead,
    status_code=status.HTTP_201_CREATED,
    tags=["user_locations"],
)
def record_user_location(
    user_id: UUID,
    payload: UserLocationCreate,
    db: Session = Depends(get_db),
) -> UserLocationRead:
    """Persist a location update reported by the mobile app."""

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user_not_found",
        )

    captured_at = payload.captured_at
    if captured_at.tzinfo is None:
        captured_at = captured_at.replace(tzinfo=timezone.utc)

    location = UserLocation(
        user_id=user_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy=payload.accuracy,
        captured_at=captured_at,
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    return UserLocationRead.model_validate(location)


@router.get(
    "/users/{user_id}/locations/latest",
    response_model=UserLocationRead,
    tags=["user_locations"],
)
def get_latest_user_location(
    user_id: UUID,
    db: Session = Depends(get_db),
) -> UserLocationRead:
    """Return the most recent location reported for the user."""

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user_not_found",
        )

    result = db.execute(
        select(UserLocation)
        .where(UserLocation.user_id == user_id)
        .order_by(
            UserLocation.captured_at.desc(),
            UserLocation.created_at.desc(),
        )
        .limit(1)
    )
    location = result.scalars().first()
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="location_not_found",
        )
    return UserLocationRead.model_validate(location)
