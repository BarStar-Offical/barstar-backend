from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VenuesBase(BaseModel):
    """Shared properties for Venues."""

    # TODO: Add your fields here
    pass


class VenuesCreate(VenuesBase):
    """Properties to receive on Venues creation."""

    pass


class VenuesUpdate(VenuesBase):
    """Properties to receive on Venues update."""

    pass


class VenuesInDB(VenuesBase):
    """Properties stored in database."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class Venues(VenuesInDB):
    """Properties to return to client."""

    pass
