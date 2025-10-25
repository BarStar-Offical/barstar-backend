from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.followers import StatusEnum


class FollowersBase(BaseModel):
    """Shared properties for Followers."""

    follower_id: UUID
    followed_id: UUID


class FollowersCreate(FollowersBase):
    """Properties to receive on Followers creation."""

    status: StatusEnum | None = None


class FollowersUpdate(BaseModel):
    """Properties to receive on Followers update."""

    status: StatusEnum | None = None


class FollowersInDB(FollowersBase):
    """Properties stored in database."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: StatusEnum = Field(default=StatusEnum.PENDING)
    created_at: datetime
    updated_at: datetime


class FollowersRead(FollowersInDB):
    """Properties to return to client."""

    pass
