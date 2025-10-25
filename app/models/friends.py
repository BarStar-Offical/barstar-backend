from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, func, CheckConstraint, select, union_all
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey

from app.db.base import Base
from app.models.users import Users


class StatusEnum(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class Friends(Base):
    """TODO: Add model description."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    # The user who requests the friendship
    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # The user who accepts the friendship
    accepter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # The status of the friendship (e.g., "pending", "accepted", "rejected")
    status: Mapped[StatusEnum] = mapped_column(
        default=StatusEnum.PENDING,
    )
    
    __table_args__ = (
        # no self-friendships
        CheckConstraint("requester_id <> accepter_id", name="friends_no_self"),
        # unique on unordered pair so (A,B) and (B,A) can't both exist
        Index(
            "uq_friends_unordered",
            func.least(requester_id, accepter_id),
            func.greatest(requester_id, accepter_id),
            unique=True,
        ),
    )
    
    @staticmethod
    def friends_ids_stmt(user_id: uuid.UUID):
        # (user_id) → accepted friends no matter who requested whom
        sent = (
            select(Friends.accepter_id.label("friend_id"))
            .where(
                Friends.requester_id == user_id,
                Friends.status == StatusEnum.ACCEPTED,
            )
        )
        received = (
            select(Friends.requester_id.label("friend_id"))
            .where(
                Friends.accepter_id == user_id,
                Friends.status == StatusEnum.ACCEPTED,
            )
        )
        return union_all(sent, received).subquery()

    @staticmethod
    def get_friends(session: Session, user_id: uuid.UUID):
        F = Friends.friends_ids_stmt(user_id)
        return session.scalars(select(Users).join(F, Users.id == F.c.friend_id)).all()