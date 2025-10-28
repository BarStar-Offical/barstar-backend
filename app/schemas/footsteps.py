from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FootstepsBase(BaseModel):
    """Shared properties for Footsteps."""
    coordinates: str
    user_id: uuid.UUID
    pass


class FootstepsCreate(FootstepsBase):
    """Properties to receive on Footsteps creation."""
    pass


class FootstepsUpdate(FootstepsBase):
    """Properties to receive on Footsteps update."""
    created_at: datetime
    updated_at: datetime
    pass


class FootstepsInDB(FootstepsBase):
    """Properties stored in database."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    coordinates: str
    user_id: uuid.UUID


class Footsteps(FootstepsInDB):
    """Properties to return to client."""
    pass
