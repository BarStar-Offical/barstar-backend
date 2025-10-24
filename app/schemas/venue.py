from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class VenueBase(BaseModel):
    """Shared properties for Venue."""
    # TODO: Add your fields here
    pass


class VenueCreate(VenueBase):
    """Properties to receive on Venue creation."""
    pass


class VenueUpdate(VenueBase):
    """Properties to receive on Venue update."""
    pass


class VenueInDB(VenueBase):
    """Properties stored in database."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class Venue(VenueInDB):
    """Properties to return to client."""
    pass
