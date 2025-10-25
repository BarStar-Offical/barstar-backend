"""add user location table

Revision ID: b50ce2e8a41a
Revises: a876e14e10d8
Create Date: 2025-11-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b50ce2e8a41a"
down_revision: Union[str, Sequence[str], None] = "a876e14e10d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add table for storing user location updates."""

    op.create_table(
        "userlocation",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("accuracy", sa.Float(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk_userlocation_user_id_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_userlocation")),
    )
    op.create_index(
        op.f("ix_userlocation_user_id_captured_at"),
        "userlocation",
        ["user_id", "captured_at"],
    )


def downgrade() -> None:
    """Remove table that stores user location updates."""

    op.drop_index(op.f("ix_userlocation_user_id_captured_at"), table_name="userlocation")
    op.drop_table("userlocation")
