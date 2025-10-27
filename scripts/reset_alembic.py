#!/usr/bin/env python3
"""Reset alembic version table."""
from app.db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    conn.commit()
    print("Dropped alembic_version table")
