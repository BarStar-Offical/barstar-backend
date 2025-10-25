from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserLocationBase(BaseModel):
    """Shared location fields with basic validation."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: float | None = Field(None, ge=0)
    captured_at: datetime


class UserLocationCreate(UserLocationBase):
    """Payload received from the mobile client when reporting location."""


class UserLocationRead(UserLocationBase):
    """Representation returned via API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
