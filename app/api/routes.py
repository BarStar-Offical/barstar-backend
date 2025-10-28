from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_task_queue
from app.models import Followers, Users
from app.models.followers import StatusEnum
from app.models.operators import OperatorRole as OperatorRoleModel
from app.models.operators import Operators as OperatorsModel
from app.models.venues import Venues as VenuesModel
from app.schemas import (
    FollowersCreate,
    FollowersRead,
    FollowersUpdate,
    OperatorsCreate,
    OperatorsRead,
    OperatorsUpdate,
    UsersCreate,
    UsersRead,
    UsersUpdate,
)
from app.schemas import Venues as VenuesRead
from app.schemas import VenuesCreate, VenuesUpdate
from app.services import TaskQueue

router = APIRouter(prefix="/api/v1")


@router.get("/health", tags=["health"])
def healthcheck(db: Session = Depends(get_db)) -> dict[str, Any]:
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
    response_model=UsersRead,
    status_code=status.HTTP_201_CREATED,
    tags=["users"],
)
def create_user(
    payload: UsersCreate,
    db: Session = Depends(get_db),
    queue: TaskQueue = Depends(get_task_queue),
) -> UsersRead:
    """Create a new user and enqueue a lightweight background event."""

    conflict = db.execute(
        select(Users)
        .where(
            or_(
                Users.email == payload.email,
                Users.oauth_provider_id == payload.oauth_provider_id,
            )
        )
        .limit(1)
    ).scalar_one_or_none()
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="user_already_exists",
        )

    user = Users(
        email=payload.email,
        full_name=payload.full_name,
        oauth_provider=payload.oauth_provider,
        oauth_provider_id=payload.oauth_provider_id,
        points=payload.points,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    queue.enqueue("user.created", {"id": str(user.id)})
    return UsersRead.model_validate(user)


@router.get(
    "/users",
    response_model=list[UsersRead],
    tags=["users"],
)
def list_users(db: Session = Depends(get_db)) -> list[UsersRead]:
    """List all users ordered by creation date."""

    result = db.execute(select(Users).order_by(Users.created_at.desc()))
    users = result.scalars().all()
    return [UsersRead.model_validate(user) for user in users]


@router.get(
    "/users/{user_id}",
    response_model=UsersRead,
    tags=["users"],
)
def get_user(user_id: UUID, db: Session = Depends(get_db)) -> UsersRead:
    """Retrieve a single user by identifier."""

    user = _get_user_or_404(db, user_id)
    return UsersRead.model_validate(user)


@router.put(
    "/users/{user_id}",
    response_model=UsersRead,
    tags=["users"],
)
def update_user(
    user_id: UUID,
    payload: UsersUpdate,
    db: Session = Depends(get_db),
    queue: TaskQueue = Depends(get_task_queue),
) -> UsersRead:
    """Update an existing user."""

    user = _get_user_or_404(db, user_id)
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return UsersRead.model_validate(user)

    if "email" in updates:
        email_conflict = db.execute(
            select(Users).where(Users.email == updates["email"], Users.id != user_id).limit(1)
        ).scalar_one_or_none()
        if email_conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="email_already_exists",
            )

    if "oauth_provider_id" in updates:
        provider_conflict = db.execute(
            select(Users)
            .where(Users.oauth_provider_id == updates["oauth_provider_id"], Users.id != user_id)
            .limit(1)
        ).scalar_one_or_none()
        if provider_conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="oauth_provider_id_already_exists",
            )

    for field, value in updates.items():
        setattr(user, field, value)

    db.add(user)
    db.commit()
    db.refresh(user)

    queue.enqueue("user.updated", {"id": str(user.id)})
    return UsersRead.model_validate(user)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["users"],
)
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    queue: TaskQueue = Depends(get_task_queue),
) -> Response:
    """Delete a user."""

    user = _get_user_or_404(db, user_id)

    user_identifier = str(user.id)

    db.delete(user)
    db.commit()

    queue.enqueue("user.deleted", {"id": user_identifier})
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/operators",
    response_model=OperatorsRead,
    status_code=status.HTTP_201_CREATED,
    tags=["operators"],
)
def create_operator(
    payload: OperatorsCreate,
    db: Session = Depends(get_db),
    queue: TaskQueue = Depends(get_task_queue),
) -> OperatorsRead:
    """Create a new operator and associate any provided venues."""

    venues = _get_venues_by_ids(db, payload.venue_ids)

    try:
        operator_role = _normalize_operator_role(payload.role)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_operator_role",
        ) from exc

    operator = OperatorsModel(
        role=operator_role,
        email=payload.email,
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        is_active=payload.is_active,
        venues=venues,
    )
    db.add(operator)
    db.commit()
    db.refresh(operator)

    queue.enqueue("operator.created", {"id": str(operator.id)})
    return _serialize_operator(operator)


@router.get(
    "/operators",
    response_model=list[OperatorsRead],
    tags=["operators"],
)
def list_operators(db: Session = Depends(get_db)) -> list[OperatorsRead]:
    """List operators ordered by creation date."""

    order_clause = (
        OperatorsModel.created_at.desc(),
        OperatorsModel.id.desc(),
    )
    result = db.execute(select(OperatorsModel).order_by(*order_clause))
    operators = result.scalars().all()
    return [_serialize_operator(operator) for operator in operators]


@router.get(
    "/operators/{operator_id}",
    response_model=OperatorsRead,
    tags=["operators"],
)
def get_operator(operator_id: UUID, db: Session = Depends(get_db)) -> OperatorsRead:
    """Retrieve a single operator by identifier."""

    operator = _get_operator_or_404(db, operator_id)
    return _serialize_operator(operator)


@router.put(
    "/operators/{operator_id}",
    response_model=OperatorsRead,
    tags=["operators"],
)
def update_operator(
    operator_id: UUID,
    payload: OperatorsUpdate,
    db: Session = Depends(get_db),
    queue: TaskQueue = Depends(get_task_queue),
) -> OperatorsRead:
    """Update an existing operator."""

    operator = _get_operator_or_404(db, operator_id)
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return _serialize_operator(operator)

    if "role" in updates and updates["role"] is not None:
        try:
            operator.role = _normalize_operator_role(updates["role"])
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid_operator_role",
            ) from exc

    if "email" in updates and updates["email"] is not None:
        operator.email = updates["email"]
    if "full_name" in updates and updates["full_name"] is not None:
        operator.full_name = updates["full_name"]
    if "phone_number" in updates:
        operator.phone_number = updates["phone_number"]
    if "is_active" in updates and updates["is_active"] is not None:
        operator.is_active = updates["is_active"]
    if "venue_ids" in updates and updates["venue_ids"] is not None:
        operator.venues = _get_venues_by_ids(db, updates["venue_ids"])

    db.add(operator)
    db.commit()
    db.refresh(operator)

    queue.enqueue("operator.updated", {"id": str(operator.id)})
    return _serialize_operator(operator)


@router.delete(
    "/operators/{operator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["operators"],
)
def delete_operator(
    operator_id: UUID,
    db: Session = Depends(get_db),
    queue: TaskQueue = Depends(get_task_queue),
) -> Response:
    """Delete an operator."""

    operator = _get_operator_or_404(db, operator_id)
    operator_identifier = str(operator.id)

    db.delete(operator)
    db.commit()

    queue.enqueue("operator.deleted", {"id": operator_identifier})
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/venues",
    response_model=VenuesRead,
    status_code=status.HTTP_201_CREATED,
    tags=["venues"],
)
def create_venue(
    payload: VenuesCreate,
    db: Session = Depends(get_db),
    queue: TaskQueue = Depends(get_task_queue),
) -> VenuesRead:
    """Create a new venue."""

    venue_data = payload.model_dump(exclude_unset=True)
    venue = VenuesModel(**venue_data)
    db.add(venue)
    db.commit()
    db.refresh(venue)

    queue.enqueue("venue.created", {"id": str(venue.id)})
    return _serialize_venue(venue)


@router.get(
    "/venues",
    response_model=list[VenuesRead],
    tags=["venues"],
)
def list_venues(db: Session = Depends(get_db)) -> list[VenuesRead]:
    """List venues ordered by creation date."""

    order_clause = (
        VenuesModel.created_at.desc(),
        VenuesModel.id.desc(),
    )
    result = db.execute(select(VenuesModel).order_by(*order_clause))
    venues = result.scalars().all()
    return [_serialize_venue(venue) for venue in venues]


@router.get(
    "/venues/{venue_id}",
    response_model=VenuesRead,
    tags=["venues"],
)
def get_venue(venue_id: UUID, db: Session = Depends(get_db)) -> VenuesRead:
    """Retrieve a single venue by identifier."""

    venue = _get_venue_or_404(db, venue_id)
    return _serialize_venue(venue)


@router.put(
    "/venues/{venue_id}",
    response_model=VenuesRead,
    tags=["venues"],
)
def update_venue(
    venue_id: UUID,
    payload: VenuesUpdate,
    db: Session = Depends(get_db),
    queue: TaskQueue = Depends(get_task_queue),
) -> VenuesRead:
    """Update an existing venue."""

    venue = _get_venue_or_404(db, venue_id)
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return _serialize_venue(venue)

    for field, value in updates.items():
        setattr(venue, field, value)

    db.add(venue)
    db.commit()
    db.refresh(venue)

    queue.enqueue("venue.updated", {"id": str(venue.id)})
    return _serialize_venue(venue)


@router.delete(
    "/venues/{venue_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["venues"],
)
def delete_venue(
    venue_id: UUID,
    db: Session = Depends(get_db),
    queue: TaskQueue = Depends(get_task_queue),
) -> Response:
    """Delete a venue."""

    venue = _get_venue_or_404(db, venue_id)
    venue_identifier = str(venue.id)

    db.delete(venue)
    db.commit()

    queue.enqueue("venue.deleted", {"id": venue_identifier})
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/followers",
    response_model=FollowersRead,
    status_code=status.HTTP_201_CREATED,
    tags=["followers"],
)
def create_follow_relationship(
    payload: FollowersCreate,
    db: Session = Depends(get_db),
    queue: TaskQueue = Depends(get_task_queue),
) -> FollowersRead:
    """Create a follower relationship between two users."""

    if payload.follower_id == payload.followed_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cannot_follow_self",
        )

    _get_user_or_404(db, payload.follower_id)
    _get_user_or_404(db, payload.followed_id)

    existing_relationship = db.execute(
        select(Followers)
        .where(
            Followers.follower_id == payload.follower_id,
            Followers.followed_id == payload.followed_id,
        )
        .limit(1)
    ).scalar_one_or_none()
    if existing_relationship is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="follow_relationship_exists",
        )

    relationship = Followers(
        follower_id=payload.follower_id,
        followed_id=payload.followed_id,
        status=payload.status or StatusEnum.PENDING,
    )
    db.add(relationship)
    db.commit()
    db.refresh(relationship)

    queue.enqueue("follow.created", {"id": str(relationship.id)})
    return FollowersRead.model_validate(relationship)


@router.get(
    "/followers",
    response_model=list[FollowersRead],
    tags=["followers"],
)
def list_follow_relationships(
    follower_id: UUID | None = None,
    followed_id: UUID | None = None,
    status_filter: StatusEnum | None = None,
    db: Session = Depends(get_db),
) -> list[FollowersRead]:
    """List follower relationships with optional filters."""

    stmt = select(Followers).order_by(Followers.created_at.desc())
    if follower_id is not None:
        stmt = stmt.where(Followers.follower_id == follower_id)
    if followed_id is not None:
        stmt = stmt.where(Followers.followed_id == followed_id)
    if status_filter is not None:
        stmt = stmt.where(Followers.status == status_filter)

    relationships = db.execute(stmt).scalars().all()
    return [FollowersRead.model_validate(relationship) for relationship in relationships]


@router.get(
    "/followers/{follow_id}",
    response_model=FollowersRead,
    tags=["followers"],
)
def get_follow_relationship(
    follow_id: UUID,
    db: Session = Depends(get_db),
) -> FollowersRead:
    """Retrieve a single follower relationship by identifier."""

    relationship = _get_follow_relationship_or_404(db, follow_id)
    return FollowersRead.model_validate(relationship)


@router.put(
    "/followers/{follow_id}",
    response_model=FollowersRead,
    tags=["followers"],
)
def update_follow_relationship(
    follow_id: UUID,
    payload: FollowersUpdate,
    db: Session = Depends(get_db),
    queue: TaskQueue = Depends(get_task_queue),
) -> FollowersRead:
    """Update a follower relationship."""

    relationship = _get_follow_relationship_or_404(db, follow_id)
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return FollowersRead.model_validate(relationship)

    if "status" in updates and updates["status"] is not None:
        relationship.status = updates["status"]

    db.add(relationship)
    db.commit()
    db.refresh(relationship)

    queue.enqueue("follow.updated", {"id": str(relationship.id)})
    return FollowersRead.model_validate(relationship)


@router.delete(
    "/followers/{follow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["followers"],
)
def delete_follow_relationship(
    follow_id: UUID,
    db: Session = Depends(get_db),
    queue: TaskQueue = Depends(get_task_queue),
) -> Response:
    """Delete a follower relationship."""

    relationship = _get_follow_relationship_or_404(db, follow_id)
    identifier = str(relationship.id)

    db.delete(relationship)
    db.commit()

    queue.enqueue("follow.deleted", {"id": identifier})
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _normalize_operator_role(role: Any) -> OperatorRoleModel:
    if isinstance(role, OperatorRoleModel):
        return role
    if isinstance(role, str):
        try:
            return OperatorRoleModel[role.upper()]
        except KeyError as exc:
            raise ValueError("Invalid operator role") from exc
    if hasattr(role, "name"):
        name = getattr(role, "name")
        if isinstance(name, str):
            try:
                return OperatorRoleModel[name]
            except KeyError:
                pass
    if hasattr(role, "value"):
        value = getattr(role, "value")
        if isinstance(value, str):
            try:
                return OperatorRoleModel[value.upper()]
            except KeyError as exc:
                raise ValueError("Invalid operator role") from exc
    raise ValueError("Invalid operator role")


def _serialize_operator(operator: OperatorsModel) -> OperatorsRead:
    try:
        role = _normalize_operator_role(operator.role)
        role_str = role.value.lower()
    except ValueError:
        role_str = str(operator.role)

    data = {
        "id": operator.id,
        "created_at": operator.created_at,
        "updated_at": operator.updated_at,
        "role": role_str,
        "email": operator.email,
        "full_name": operator.full_name,
        "phone_number": operator.phone_number,
        "is_active": operator.is_active,
        "venue_ids": operator.venue_ids,
    }
    return OperatorsRead.model_validate(data)


def _serialize_venue(venue: VenuesModel) -> VenuesRead:
    return VenuesRead.model_validate(venue)


def _get_operator_or_404(db: Session, operator_id: UUID) -> OperatorsModel:
    operator = db.get(OperatorsModel, operator_id)
    if operator is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="operator_not_found",
        )
    return operator


def _get_venue_or_404(db: Session, venue_id: UUID) -> VenuesModel:
    venue = db.get(VenuesModel, venue_id)
    if venue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="venue_not_found",
        )
    return venue


def _get_venues_by_ids(db: Session, venue_ids: list[UUID]) -> list[VenuesModel]:
    venues: list[VenuesModel] = []
    for venue_id in venue_ids:
        venues.append(_get_venue_or_404(db, venue_id))
    return venues


def _get_user_or_404(db: Session, user_id: UUID) -> Users:
    user = db.get(Users, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user_not_found",
        )
    return user


def _get_follow_relationship_or_404(db: Session, follow_id: UUID) -> Followers:
    relationship = db.execute(
        select(Followers).where(Followers.id == follow_id).limit(1)
    ).scalar_one_or_none()
    if relationship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="follow_relationship_not_found",
        )
    return relationship


if __name__ == "__main__":
    print("Running routes.py")
