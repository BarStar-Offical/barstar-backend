#!/usr/bin/env python3
"""Drop all tables and reset the database."""
from app.db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Drop all tables
    conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS venue CASCADE"))
    conn.execute(text('DROP TABLE IF EXISTS "user" CASCADE'))
    conn.commit()
    print("All tables dropped - database is clean")
