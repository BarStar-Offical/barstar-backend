from sqlalchemy import text
from app.db.session import SessionLocal

with SessionLocal() as session:
    rows = session.execute(
        text("SELECT extname, extversion FROM pg_extension WHERE extname IN ('postgis','age');")
    ).all()
    print(rows)