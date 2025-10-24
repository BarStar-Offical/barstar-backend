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
