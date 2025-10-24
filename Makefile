VENV ?= .venv
PYTHON ?= python3.11
BIN := $(VENV)/bin

.PHONY: install install-dev fmt lint test migrations-up migrations-down

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip setuptools wheel
	$(BIN)/pip install .

install-dev:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip setuptools wheel
	$(BIN)/pip install -e ".[dev]"

fmt:
	$(BIN)/ruff check --select I --fix .
	$(BIN)/black .

lint:
	$(BIN)/ruff check .
	$(BIN)/mypy .

test:
	$(BIN)/pytest

migrations-up:
	$(BIN)/alembic upgrade head

migrations-down:
	$(BIN)/alembic downgrade -1

create-table:
	@if [ -z "$(name)" ]; then \
		echo "Usage: make create-table name=<table_name>"; \
		echo "Example: make create-table name=venue"; \
		exit 1; \
	fi
	$(BIN)/python scripts/create_table.py $(name)

db-init:
	$(BIN)/alembic downgrade base
	$(BIN)/alembic upgrade head
	$(BIN)/alembic revision --autogenerate -m "initial schema"

db-reset:
	$(BIN)/alembic downgrade base
	$(BIN)/alembic upgrade head

db-seed:
	$(BIN)/python scripts/seed_db.py

db-seed-clear:
	$(BIN)/python scripts/seed_db.py --clear

db-refresh: db-reset db-seed
	@echo "✅ Database refreshed with seed data"
