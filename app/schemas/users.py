from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UsersBase(BaseModel):
    email: EmailStr
    full_name: str
    oauth_provider: str
    oauth_provider_id: str
    points: int = 0


class UsersCreate(UsersBase):
    """Payload for creating users."""


class UsersUpdate(BaseModel):
    """Payload for updating users."""

    email: EmailStr | None = None
    full_name: str | None = None
    oauth_provider: str | None = None
    oauth_provider_id: str | None = None
    points: int | None = None


class UsersRead(UsersBase):
    """Representation returned via API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
