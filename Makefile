VENV ?= .venv
UV ?= uv
BIN := $(VENV)/bin

.PHONY: install install-dev fmt lint test migrations-up migrations-down

install:
	$(UV) sync --locked

install-dev:
	@# Check for lock file
	@if [ -f uv.lock ]; then \
		uv sync --locked --extra dev; \
	else \
		read -p "No uv.lock file found. Do you want to install Python dependencies anyways? (y/n): " answer; \
		if [ "$$answer" = "y" ]; then \
			uv sync --extra dev; \
		else \
			echo "Skipped installing Python dependencies."; \
		fi; \
	fi

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
	$(BIN)/alembic downgrade base > /dev/null
	@if [ -z "$$(find alembic/versions -maxdepth 1 -type f ! -name '*.pyc' -print -quit)" ]; then \
		echo "✅ Alembic versions directory is empty. Initializing database...🔥"; \
	else \
		printf "❌ Nah bro, your alembic versions directory is not empty. You want to fuck your shit up or do you want to clean it up now? "; \
		read choice; \
		case $$choice in \
			[Yy]* ) echo "bet, deleting your alembic shit ..."; rm -rf alembic/versions/*;; \
			[Nn]* ) echo "Make up your fucking mind!"; exit 1;; \
			* ) echo "What the fuck does that mean??"; exit 1;; \
		esac; \
	fi
	$(BIN)/alembic upgrade head > /dev/null
	$(BIN)/alembic revision --autogenerate -m "initial schema" > /dev/null
	$(BIN)/alembic upgrade head > /dev/null
	@echo "Shit yeah bud👍! Database initialized with initial schema"

db-reset:
	$(BIN)/alembic downgrade base
	$(BIN)/alembic upgrade head

db-seed:
	$(BIN)/python scripts/seed_db.py

db-seed-clear:
	$(BIN)/python scripts/seed_db.py --clear

db-refresh: db-reset db-seed
	@echo "✅ Database refreshed with seed data"
