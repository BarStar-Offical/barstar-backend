from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Table, func
from sqlalchemy.dialects.postgresql import UUID, CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:  # pragma: no cover - aid static type analysis
    from app.models.venues import Venues


class OperatorRole(enum.Enum):
    """Roles that an operator can perform for a venue."""

    OWNER = "OWNER"
    STAFF = "STAFF"


operator_venues = Table(
    "operator_venues",
    Base.metadata,
    Column(
        "operator_id",
        UUID(as_uuid=True),
        ForeignKey("operators.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "venue_id",
        UUID(as_uuid=True),
        ForeignKey("venues.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Operators(Base):
    """Venue operators such as staff members and owners."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=func.now(),
    )
    role: Mapped[OperatorRole] = mapped_column(
        Enum(OperatorRole, name="operatorrole"),
        nullable=False,
        default=OperatorRole.STAFF,
    )
    email: Mapped[str] = mapped_column(CITEXT(), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(length=255))
    phone_number: Mapped[str] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True)
    # SQLAlchemy relationship allowing operators to manage multiple venues.
    venues: Mapped[list[Venues]] = relationship(
        "Venues",
        secondary=operator_venues,
        back_populates="operators",
    )

    @property
    def venue_ids(self) -> list[uuid.UUID]:
        """Convenience accessor exposing related venue identifiers."""
        return [venue.id for venue in self.venues]
