from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class VenuesBase(BaseModel):
    """Shared properties for Venues."""

    coordinates: str | None = None
    area: str | None = None
    name: str | None = None
    description: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    area_code: str | None = None
    country: str | None = None
    website: str | None = None
    phone_number: str | None = None
    email: EmailStr | None = None
    capacity: int | None = None
    indoor: bool | None = None
    outdoor: bool | None = None
    parking_available: bool | None = None
    wheelchair_accessible: bool | None = None
    vip_area: bool | None = None
    age_restriction: int | None = None
    smoking_allowed: bool | None = None
    alcohol_served: bool | None = None
    food_served: bool | None = None
    live_music: bool | None = None
    dance_floor: bool | None = None
    dress_code: str | None = None
    opening_hours: str | None = None
    tags: str | None = None
    rating: float | None = None
    number_of_reviews: int | None = None
    price_range: str | None = None
    owner_id: uuid.UUID | None = None
    is_active: bool | None = None
    is_verified: bool | None = None
    verification_date: datetime | None = None
    verified_by: uuid.UUID | None = None
    experience_points: int | None = None
    photo_url: str | None = None


class VenuesCreate(VenuesBase):
    """Properties to receive on Venues creation."""
    pass

class VenuesUpdate(BaseModel):
    """Properties to receive on Venues update."""

    coordinates: str | None = None
    area: str | None = None
    name: str | None = None
    description: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    area_code: str | None = None
    country: str | None = None
    website: str | None = None
    phone_number: str | None = None
    email: EmailStr | None = None
    capacity: int | None = None
    indoor: bool | None = None
    outdoor: bool | None = None
    parking_available: bool | None = None
    wheelchair_accessible: bool | None = None
    vip_area: bool | None = None
    age_restriction: int | None = None
    smoking_allowed: bool | None = None
    alcohol_served: bool | None = None
    food_served: bool | None = None
    live_music: bool | None = None
    dance_floor: bool | None = None
    dress_code: str | None = None
    opening_hours: str | None = None
    tags: str | None = None
    rating: float | None = None
    number_of_reviews: int | None = None
    price_range: str | None = None
    owner_id: uuid.UUID | None = None
    is_active: bool | None = None
    is_verified: bool | None = None
    verification_date: datetime | None = None
    verified_by: uuid.UUID | None = None
    experience_points: int | None = None
    photo_url: str | None = None


class VenuesInDB(VenuesBase):
    """Properties stored in database."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class Venues(VenuesInDB):
    """Properties to return to client."""

    pass
