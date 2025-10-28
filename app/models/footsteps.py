from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Footsteps(Base):
    """A table to hold user footsteps data."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),       
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    coordinates: Mapped[str] = mapped_column(default="POINT(0 0)")
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )

# Since we will often query recently created footsteps, we add an index on created_at in descending order
Index("ix_footsteps_created_at_desc", Footsteps.created_at.desc())

