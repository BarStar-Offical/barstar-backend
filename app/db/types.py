from __future__ import annotations

from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.types import Text, TypeDecorator

__all__ = ["CaseInsensitiveText"]


class CaseInsensitiveText(TypeDecorator[str]):
    """CITEXT on PostgreSQL with a portable TEXT fallback for other dialects."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):  # type: ignore[override]
        if dialect.name == "postgresql":
            return dialect.type_descriptor(CITEXT())
        print("Using fallback TEXT type for CaseInsensitiveText")
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):  # type: ignore[override]
        return value

    def process_result_value(self, value, dialect):  # type: ignore[override]
        return value
