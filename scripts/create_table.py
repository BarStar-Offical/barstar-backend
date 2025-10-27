#!/usr/bin/env python3
"""Generate boilerplate for a new database table/model."""

import argparse
import re
import sys
from pathlib import Path


def to_snake_case(name: str) -> str:
    """Convert CamelCase to snake_case."""
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.lower()


def to_pascal_case(name: str) -> str:
    """Convert snake_case to PascalCase."""
    return "".join(word.capitalize() for word in name.split("_"))


MODEL_TEMPLATE = '''from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class {class_name}(Base):
    """TODO: Add model description."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    # TODO: Add your columns here
    # Example:
    # name: Mapped[str] = mapped_column(nullable=False)
    # description: Mapped[str | None] = mapped_column(nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
'''

SCHEMA_TEMPLATE = '''from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class {class_name}Base(BaseModel):
    """Shared properties for {class_name}."""
    # TODO: Add your fields here
    pass


class {class_name}Create({class_name}Base):
    """Properties to receive on {class_name} creation."""
    pass


class {class_name}Update({class_name}Base):
    """Properties to receive on {class_name} update."""
    pass


class {class_name}InDB({class_name}Base):
    """Properties stored in database."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class {class_name}({class_name}InDB):
    """Properties to return to client."""
    pass
'''


def create_model(name: str, base_dir: Path) -> None:
    """Create a new model file."""
    class_name = to_pascal_case(name)
    file_name = to_snake_case(name)

    model_path = base_dir / "app" / "models" / f"{file_name}.py"

    if model_path.exists():
        print(f"❌ Model already exists: {model_path}")
        sys.exit(1)

    model_path.write_text(MODEL_TEMPLATE.format(class_name=class_name))
    print(f"✅ Created model: {model_path}")


def create_schema(name: str, base_dir: Path) -> None:
    """Create a new schema file."""
    class_name = to_pascal_case(name)
    file_name = to_snake_case(name)

    schema_path = base_dir / "app" / "schemas" / f"{file_name}.py"

    if schema_path.exists():
        print(f"❌ Schema already exists: {schema_path}")
        sys.exit(1)

    schema_path.write_text(SCHEMA_TEMPLATE.format(class_name=class_name))
    print(f"✅ Created schema: {schema_path}")


def update_init_files(name: str, base_dir: Path) -> None:
    """Update __init__.py files to export the new model and schema."""
    class_name = to_pascal_case(name)
    file_name = to_snake_case(name)

    # Update models/__init__.py
    models_init = base_dir / "app" / "models" / "__init__.py"
    if models_init.exists():
        content = models_init.read_text()
        if class_name not in content:
            import_line = f"from app.models.{file_name} import {class_name}\n"
            if content.strip():
                content += import_line
            else:
                content = import_line
            models_init.write_text(content)
            print(f"✅ Updated: {models_init}")

    # Update schemas/__init__.py
    schemas_init = base_dir / "app" / "schemas" / "__init__.py"
    if schemas_init.exists():
        content = schemas_init.read_text()
        if class_name not in content:
            import_line = f"from app.schemas.{file_name} import {class_name}, {class_name}Create, {class_name}Update\n"
            if content.strip():
                content += import_line
            else:
                content = import_line
            schemas_init.write_text(content)
            print(f"✅ Updated: {schemas_init}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate boilerplate for a new database table/model"
    )
    parser.add_argument(
        "name",
        help="Name of the model (in snake_case or PascalCase)",
    )
    parser.add_argument(
        "--model-only",
        action="store_true",
        help="Only create the model file",
    )
    parser.add_argument(
        "--schema-only",
        action="store_true",
        help="Only create the schema file",
    )

    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent

    print(f"\n📦 Creating boilerplate for: {args.name}\n")

    if args.schema_only:
        create_schema(args.name, base_dir)
    elif args.model_only:
        create_model(args.name, base_dir)
    else:
        create_model(args.name, base_dir)
        create_schema(args.name, base_dir)
        update_init_files(args.name, base_dir)

    table_name = to_snake_case(args.name)
    print(f"\n✨ Next steps:")
    print(f"   1. Edit the model in app/models/{table_name}.py")
    print(f"   2. Edit the schema in app/schemas/{table_name}.py")
    print(
        f"   3. Generate migration: alembic revision --autogenerate -m 'Create {table_name} table'"
    )
    print(f"   4. Apply migration: alembic upgrade head\n")


if __name__ == "__main__":
    main()
