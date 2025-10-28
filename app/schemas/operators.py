from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OperatorRole(str, enum.Enum):
    """Roles that an operator can perform for a venue."""

    OWNER = "owner"
    STAFF = "staff"


class OperatorsBase(BaseModel):
    """Shared properties across operator schemas."""

    role: OperatorRole
    email: EmailStr
    full_name: str
    phone_number: str | None
    venue_ids: list[UUID]
    is_active: bool


class OperatorsCreate(OperatorsBase):
    """Payload accepted when creating an operator."""


class OperatorsUpdate(BaseModel):
    """Payload accepted when updating an operator."""

    role: OperatorRole | None
    email: EmailStr | None
    full_name: str | None
    phone_number: str | None
    venue_ids: list[UUID] | None
    is_active: bool | None


class OperatorsRead(OperatorsBase):
    """Representation returned from API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
