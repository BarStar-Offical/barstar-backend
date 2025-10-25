from __future__ import annotations

from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UsersBase(BaseModel):
    email: EmailStr
    full_name: str
    oauth_provider: str
    oauth_provider_id: str


class UsersCreate(UsersBase):
    """Payload for creating users."""


class UsersRead(UsersBase):
    """Representation returned via API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    points: int
