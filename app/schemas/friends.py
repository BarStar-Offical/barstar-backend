from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.friends import StatusEnum


class FriendsBase(BaseModel):
    """Shared properties for Friends."""
    # TODO: Add your fields here
    pass


class FriendsCreate(FriendsBase):
    """Properties to receive on Friends creation."""
    pass


class FriendsUpdate(FriendsBase):
    """Properties to receive on Friends update."""
    pass


class FriendsInDB(FriendsBase):
    """Properties stored in database."""
    
    model_config = ConfigDict(from_attributes=True)
    
    created_at: datetime
    updated_at: datetime
    requester_id: uuid.UUID
    accepter_id: uuid.UUID
    status: StatusEnum
    

class Friends(FriendsInDB):
    """Properties to return to client."""
    pass
