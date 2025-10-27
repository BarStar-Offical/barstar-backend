from __future__ import annotations

import uuid
from datetime import datetime, timezone

from citext import CIText
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.followers import Followers

CIText.cache_ok = True  # type: ignore[attr-defined]


class Users(Base):
    """Users model that can be extended with profile attributes."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[CIText] = mapped_column(CIText(), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(default="")
    oauth_provider: Mapped[str] = mapped_column(default="local")
    oauth_provider_id: Mapped[str] = mapped_column(
        unique=True,
        default=lambda: uuid.uuid4().hex,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=func.now(),
    )
    points: Mapped[int] = mapped_column(default=0, nullable=False)

    # People this user follows (A → B)
    following: Mapped[list[Users]] = relationship(
        "Users",
        secondary="followers",
        primaryjoin=id == Followers.follower_id,
        secondaryjoin=id == Followers.followed_id,
        back_populates="followers",
    )

    # People who follow this user (B ← A)
    followers: Mapped[list[Users]] = relationship(
        "Users",
        secondary="followers",
        primaryjoin=id == Followers.followed_id,
        secondaryjoin=id == Followers.follower_id,
        back_populates="following",
    )
