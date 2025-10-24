"""Drop all tables and reset the database."""
from sqlalchemy import text
from app.db.session import engine

with engine.connect() as conn:
    # Drop all tables
    conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS venue CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS \"user\" CASCADE"))
    conn.commit()
    print("All tables dropped - database is clean")
