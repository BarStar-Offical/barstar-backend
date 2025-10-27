from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.operators import operator_venues

if TYPE_CHECKING:  # pragma: no cover - aid static type analysis
    from app.models.operators import Operators


class Venues(Base):
    """TODO: Add model description."""

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    # Uses the PostGIS Extension for location data. There is a coordinate that we use for distace
    # calculations and geometry for boundary calculations.
    coordinates: Mapped[str] = mapped_column(default="POINT(0 0)")
    area: Mapped[str | None] = mapped_column(default="POLYGON((0 0,0 0,0 0,0 0))")
    name: Mapped[str] = mapped_column()
    description: Mapped[str | None] = mapped_column()
    address: Mapped[str | None] = mapped_column()
    city: Mapped[str | None] = mapped_column()
    state: Mapped[str | None] = mapped_column()
    area_code: Mapped[str | None] = mapped_column()
    country: Mapped[str | None] = mapped_column()
    website: Mapped[str | None] = mapped_column()
    phone_number: Mapped[str | None] = mapped_column()
    email: Mapped[str] = mapped_column()
    capacity: Mapped[int | None] = mapped_column()
    indoor: Mapped[bool | None] = mapped_column()
    outdoor: Mapped[bool | None] = mapped_column()
    parking_available: Mapped[bool | None] = mapped_column()
    wheelchair_accessible: Mapped[bool | None] = mapped_column()
    vip_area: Mapped[bool | None] = mapped_column()
    age_restriction: Mapped[int | None] = mapped_column()
    smoking_allowed: Mapped[bool | None] = mapped_column()
    alcohol_served: Mapped[bool | None] = mapped_column()
    food_served: Mapped[bool | None] = mapped_column()
    live_music: Mapped[bool | None] = mapped_column()
    dance_floor: Mapped[bool | None] = mapped_column()
    dress_code: Mapped[str | None] = mapped_column()
    opening_hours: Mapped[str | None] = mapped_column()
    tags: Mapped[str | None] = mapped_column()
    rating: Mapped[float | None] = mapped_column()
    number_of_reviews: Mapped[int | None] = mapped_column()
    price_range: Mapped[str | None] = mapped_column()
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    is_active: Mapped[bool] = mapped_column(default=True)
    is_verified: Mapped[bool | None] = mapped_column()
    verification_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    verified_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    experience_points: Mapped[int] = mapped_column()
    photo_url: Mapped[str | None] = mapped_column(default="")

    operators: Mapped[list[Operators]] = relationship(
        "Operators",
        secondary=operator_venues,
        back_populates="venues",
    )
