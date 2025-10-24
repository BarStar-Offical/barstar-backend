from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(str(settings.database_url), future=True, pool_pre_ping=True)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    future=True,
)


def get_db_session() -> Generator[Session, None, None]:
    """Yield a database session for request-scoped usage."""

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
