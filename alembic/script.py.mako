"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, Sequence[str], None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}

def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    for extension in ("postgis", "age", "citext"):
        bind.exec_driver_sql(f"CREATE EXTENSION IF NOT EXISTS {extension}")
    bind = op.get_bind()
    status_enum = sa.Enum(name='statusenum')
    status_enum.drop(bind, checkfirst=True)
    operator_role_enum = sa.Enum(name='operatorrole')
    operator_role_enum.drop(bind, checkfirst=True)
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Downgrade schema."""
    ${downgrades if downgrades else "pass"}
    op.execute("DROP EXTENSION IF EXISTS age")
    op.execute("DROP EXTENSION IF EXISTS postgis")
    bind = op.get_bind()
    status_enum = sa.Enum(name='statusenum')
    status_enum.drop(bind, checkfirst=True)
    operator_role_enum = sa.Enum(name='operatorrole')
    operator_role_enum.drop(bind, checkfirst=True)  

