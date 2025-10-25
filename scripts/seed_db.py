#!/usr/bin/env python3
"""Seed the database with reflection-driven, fake data.

The seeder inspects the SQLAlchemy mapper registry to discover models, infer
relationships, and generate coherent records without hand-written fixtures.
"""
from __future__ import annotations

import argparse
import contextlib
import enum
import importlib
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol, cast

from faker import Faker
from sqlalchemy import Column, Table, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql import sqltypes
from tqdm.auto import tqdm as _tqdm


class _ProgressProtocol(Protocol):
    def update(self, n: int = 1) -> None: ...

    def set_postfix(
        self, ordered_dict: dict[str, object] | None = None, refresh: bool | None = None
    ) -> None: ...

    def close(self) -> None: ...


from app.db.base import Base
from app.db.session import SessionLocal

importlib.import_module("app.models")


class RandomData:
    """Generate repeatable random data with an optional Faker backend."""

    _providers = ("google", "apple", "facebook", "github")

    def __init__(self) -> None:
        self._faker: Any | None = None
        faker_instance = cast(Any, Faker())
        faker_instance.seed_instance(random.randint(1, 1_000_000))
        self._faker = faker_instance

    def email(self) -> str:
        if self._faker is not None:
            return self._faker.unique.email()
        return f"user_{uuid.uuid4().hex[:10]}@example.com"

    def full_name(self) -> str:
        if self._faker is not None:
            return self._faker.name()
        return f"User {uuid.uuid4().hex[:6]}"

    def oauth_provider(self) -> str:
        if self._faker is not None:
            return self._faker.random_element(elements=self._providers)
        return random.choice(self._providers)

    def token(self) -> str:
        if self._faker is not None:
            return self._faker.sha256(raw_output=False)
        return uuid.uuid4().hex

    def sentence(self, words: int = 6) -> str:
        if self._faker is not None:
            return self._faker.sentence(nb_words=words)
        return " ".join(f"word{random.randint(0, 9_999)}" for _ in range(words))

    def datetime(self) -> datetime:
        if self._faker is not None:
            return self._faker.date_time_between(
                start_date="-2y", end_date="now", tzinfo=timezone.utc
            )
        return datetime.now(timezone.utc) - timedelta(
            days=random.randint(0, 730), seconds=random.randint(0, 86_400)
        )

    def integer(self, min_value: int = 0, max_value: int = 1_000) -> int:
        if self._faker is not None:
            return self._faker.random_int(min=min_value, max=max_value)
        return random.randint(min_value, max_value)

    def float(self, min_value: float = 0.0, max_value: float = 100.0) -> float:
        if self._faker is not None:
            return self._faker.pyfloat(min_value=min_value, max_value=max_value, positive=True)
        return random.uniform(min_value, max_value)

    def boolean(self) -> bool:
        if self._faker is not None:
            return bool(self._faker.boolean())
        return random.choice([True, False])

    def enum(self, enum_type: sqltypes.Enum) -> Any:
        enum_class = getattr(enum_type, "enum_class", None)
        if enum_class is not None and issubclass(enum_class, enum.Enum):
            return random.choice(list(enum_class))
        return random.choice(list(enum_type.enums))


class ReflectionSeeder:
    """Seed models discovered through SQLAlchemy reflection."""

    def __init__(
        self,
        *,
        include_models: list[str] | None = None,
        number_of_records: int = 10,
        max_attempts: int = 5,
    ) -> None:
        self.include_filters: set[str] = (
            {item.lower() for item in include_models} if include_models else set()
        )
        self.number_of_records = max(1, number_of_records)
        self.max_attempts = max(1, max_attempts)
        self.random = RandomData()
        self.metadata = Base.metadata
        self._table_model_map, self.tables = self._build_table_model_map()
        self.sorted_table_names = [
            table.name for table in self.metadata.sorted_tables if table.name in self.tables
        ]
        if not self.sorted_table_names:
            raise ValueError("No SQLAlchemy models matched the provided filters.")
        self.session_factory = SessionLocal
        self.session: Session | None = None
        self.lookup_limit = 100

    def clear_existing_data(self) -> None:
        with self.session_factory() as session:
            for table_name in reversed(self.sorted_table_names):
                session.execute(delete(self.tables[table_name]))
            session.commit()

    def generate(self) -> None:
        with self.session_factory() as session:
            self.session = session
            for table_name in self.sorted_table_names:
                model = self._table_model_map[table_name]
                table = self.tables[table_name]
                created = 0
                skipped = 0
                progress: _ProgressProtocol | None = None
                progress = cast(
                    _ProgressProtocol,
                    _tqdm(
                        total=self.number_of_records,
                        desc=f"Seeding {model.__name__}",
                        unit="record",
                        leave=False,
                    ),
                )
                for _ in range(self.number_of_records):
                    success = False
                    for _attempt in range(self.max_attempts):
                        row_data = self._generate_fake_row_data(table)
                        if row_data is None:
                            continue
                        if self._persist(model, row_data):
                            created += 1
                            success = True
                            break
                    if not success:
                        skipped += 1
                    if progress is not None:
                        progress.update(1)
                        progress.set_postfix({"created": created, "skipped": skipped})
                if progress is not None:
                    progress.close()
                print(f"  ↳ {model.__name__}: created {created}, skipped {skipped}")
            self.session = None

    def _persist(self, model: type[Any], row_data: dict[str, Any]) -> bool:
        if self.session is None:
            raise RuntimeError("Session unavailable while persisting data.")
        instance = model(**row_data)
        self.session.add(instance)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            return False
        return True

    def _build_table_model_map(self) -> tuple[dict[str, type[Any]], dict[str, Table]]:
        mapping: dict[str, type[Any]] = {}
        tables: dict[str, Table] = {}
        for mapper in Base.registry.mappers:
            class_ = mapper.class_
            table_obj = cast(Table, mapper.local_table)
            table_name = table_obj.name
            if not self._is_included(table_name, class_.__name__):
                continue
            mapping[table_name] = class_
            tables[table_name] = table_obj
        return mapping, tables

    def _is_included(self, table_name: str, class_name: str) -> bool:
        if not self.include_filters:
            return True
        variants = {
            table_name.lower(),
            class_name.lower(),
            self._snake_to_pascal_case(table_name).lower(),
        }
        return not variants.isdisjoint(self.include_filters)

    def _generate_fake_row_data(
        self,
        table: Table,
        recursion_stack: set[str] | None = None,
    ) -> dict[str, Any] | None:
        if self.session is None:
            raise RuntimeError("Session unavailable while generating data.")
        active_stack = recursion_stack or set()
        if table.name in active_stack:
            return None
        active_stack.add(table.name)
        row_data: dict[str, Any] = {}
        for column in table.columns:
            if column.name in row_data:
                continue
            if not self._should_populate_column(column):
                continue
            if column.foreign_keys:
                value = self._generate_foreign_key_value(table, column, row_data, active_stack)
            else:
                value = self._generate_scalar_value(column, row_data)
            if value is None:
                if not column.nullable and column.default is None and column.server_default is None:
                    active_stack.discard(table.name)
                    return None
                continue
            row_data[column.name] = value
        active_stack.discard(table.name)
        return row_data

    def _generate_foreign_key_value(
        self,
        table: Table,
        column: Column[Any],
        current_row: dict[str, Any],
        recursion_stack: set[str],
    ) -> Any | None:
        if self.session is None:
            raise RuntimeError("Session unavailable while generating foreign keys.")
        fk = next(iter(column.foreign_keys))
        target_table_name = fk.column.table.name
        target_model = self._table_model_map.get(target_table_name)
        if target_model is None:
            return None
        candidate = self._choose_existing_foreign_key(
            target_model, fk.column.name, table, column, current_row
        )
        if candidate is not None:
            return candidate
        if target_table_name in recursion_stack:
            return None
        target_table = self.tables[target_table_name]
        nested_data = self._generate_fake_row_data(target_table, recursion_stack)
        if nested_data is None:
            return None
        nested_instance = target_model(**nested_data)
        self.session.add(nested_instance)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            return self._choose_existing_foreign_key(
                target_model, fk.column.name, table, column, current_row
            )
        return getattr(nested_instance, fk.column.name)

    def _choose_existing_foreign_key(
        self,
        target_model: type[Any],
        column_name: str,
        table: Table,
        column: Column[Any],
        current_row: dict[str, Any],
    ) -> Any | None:
        if self.session is None:
            raise RuntimeError("Session unavailable while choosing foreign keys.")
        target_attr = getattr(target_model, column_name)
        stmt = select(target_attr).limit(self.lookup_limit)
        candidates = list(self.session.scalars(stmt).all())
        random.shuffle(candidates)
        fk_table_name = next(iter(column.foreign_keys)).column.table.name
        for value in candidates:
            if self._conflicts_with_row(table, fk_table_name, value, current_row):
                continue
            return value
        return None

    def _conflicts_with_row(
        self,
        table: Table,
        fk_table_name: str,
        candidate: Any,
        current_row: dict[str, Any],
    ) -> bool:
        for other_name, other_value in current_row.items():
            if other_value is None:
                continue
            other_column = table.columns.get(other_name)
            if other_column is None or not other_column.foreign_keys:
                continue
            for other_fk in other_column.foreign_keys:
                if other_fk.column.table.name == fk_table_name and other_value == candidate:
                    return True
        return False

    def _generate_scalar_value(
        self, column: Column[Any], _current_row: dict[str, Any]
    ) -> Any | None:
        python_type = self._python_type(column)
        name = column.name.lower()
        if python_type is uuid.UUID:
            return uuid.uuid4()
        if python_type is str and name.endswith("_id"):
            return uuid.uuid4().hex
        if "email" in name:
            return self.random.email()
        if name.endswith("name") or "full_name" in name:
            return self.random.full_name()
        if "provider" in name and python_type is str:
            return self.random.oauth_provider()
        if "token" in name:
            return self.random.token()
        if isinstance(column.type, sqltypes.Enum):
            return self.random.enum(column.type)
        if isinstance(column.type, sqltypes.Boolean):
            return self.random.boolean()
        if isinstance(column.type, (sqltypes.Integer, sqltypes.BigInteger)):
            return self.random.integer()
        if isinstance(column.type, (sqltypes.Float, sqltypes.Numeric)):
            return self.random.float()
        if isinstance(column.type, sqltypes.DateTime):
            return self.random.datetime()
        if isinstance(column.type, sqltypes.Date):
            return self.random.datetime().date()
        if isinstance(column.type, sqltypes.Time):
            return self.random.datetime().time()
        if isinstance(column.type, sqltypes.Interval):
            return timedelta(seconds=self.random.integer(0, 86_400))
        if isinstance(column.type, sqltypes.String):
            return self.random.sentence()
        if python_type is str:
            return self.random.sentence()
        if python_type is int:
            return self.random.integer()
        if python_type is float:
            return self.random.float()
        return None

    def _should_populate_column(self, column: Column[Any]) -> bool:
        if column.foreign_keys:
            return True
        if isinstance(column.type, sqltypes.Enum):
            return True
        if column.server_default is not None:
            return False
        if column.default is not None:
            return column.unique is True
        return True

    @staticmethod
    def _python_type(column: Column[Any]) -> type[Any] | None:
        with contextlib.suppress(NotImplementedError):
            return column.type.python_type
        return None

    @staticmethod
    def _snake_to_pascal_case(name: str) -> str:
        return "".join(part.capitalize() for part in name.split("_"))


def _collect_requested_models(args: argparse.Namespace) -> list[str] | None:
    explicit = set(args.models or [])
    if args.users:
        explicit.add("Users")
    if args.venues:
        explicit.add("Venues")
    if args.friends:
        explicit.add("Friends")
    return sorted(explicit) if explicit else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the database using reflection")
    parser.add_argument("--clear", action="store_true", help="Clear existing rows before seeding")
    parser.add_argument(
        "--no-seed",
        action="store_true",
        help="Skip data generation after performing preparatory steps",
    )
    parser.add_argument(
        "--records",
        type=int,
        default=10,
        help="Number of records to generate per model (default: 10)",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        help="Specific model class or table names to seed (defaults to all)",
    )
    parser.add_argument("--users", action="store_true", help="Convenience alias for Users model")
    parser.add_argument("--venues", action="store_true", help="Convenience alias for Venues model")
    parser.add_argument(
        "--friends", action="store_true", help="Convenience alias for Friends model"
    )
    args = parser.parse_args()

    try:
        seeder = ReflectionSeeder(
            include_models=_collect_requested_models(args),
            number_of_records=args.records,
        )
    except ValueError as exc:
        print(f"❌ {exc}")
        return 1

    print("🌱 Starting database seeding...")

    if args.clear:
        print("🧹 Clearing selected tables...")
        seeder.clear_existing_data()
        if args.no_seed:
            print("✅ Selected tables cleared. No new data generated.")
            return 0

    if args.no_seed:
        print("ℹ️ --no-seed specified without data generation. Nothing to do.")
        return 0

    try:
        seeder.generate()
    except Exception as exc:  # pragma: no cover - defensive guard
        if seeder.session is not None:
            seeder.session.rollback()
        print(f"❌ Error while seeding: {exc}")
        return 1

    print("✅ Database seeding completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
