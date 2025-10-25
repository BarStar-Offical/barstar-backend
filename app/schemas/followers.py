from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FollowersBase(BaseModel):
    """Shared properties for Followers."""
    # TODO: Add your fields here
    pass


class FollowersCreate(FollowersBase):
    """Properties to receive on Followers creation."""
    pass


class FollowersUpdate(FollowersBase):
    """Properties to receive on Followers update."""
    pass


class FollowersInDB(FollowersBase):
    """Properties stored in database."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class Followers(FollowersInDB):
    """Properties to return to client."""
    pass
