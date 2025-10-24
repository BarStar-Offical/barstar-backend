# Barstar Backend

FastAPI service backed by PostgreSQL, Redis, and Alembic migrations. The goal is to keep the foundation simple while providing enough structure for a productive developer experience.

## Tech Stack
- FastAPI + Uvicorn for the HTTP API
- SQLAlchemy 2.0 ORM with PostgreSQL
- Alembic migrations
- Redis-backed task queue stub
- Hatch (PEP 621) project metadata with plain `pip` install
- Tooling: Ruff, Black, MyPy, and Pytest

## Prerequisites
- Python 3.11
- `pip` and `virtualenv` (or `python -m venv`)
- Docker + Docker Compose v2 (for local infrastructure)

## 5‑Minute Local Setup
1. Copy the environment template and adjust as needed:
   ```bash
   cd backend
   cp .env.example .env
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -e ".[dev]"
   ```
   The provided `Makefile` wraps the above as `make install-dev`.
3. Start backing services and run the API:
   ```bash
   # in project root
   docker compose -f deploy/docker-compose.yaml up db redis -d

   # back in backend/
   alembic upgrade head
   uvicorn app.main:app --reload
   ```
4. Visit http://localhost:8000/docs to explore the automatically generated API docs.

## Developer Tooling
- `make fmt` → format imports and code with Ruff + Black.
- `make lint` → static analysis with Ruff and MyPy.
- `make test` → run the Pytest suite.
- `make migrations-up` / `make migrations-down` → apply or rollback Alembic migrations.

All commands assume the virtual environment located in `.venv`. Update the `Makefile` variables if you standardize on a different path.

## Database Workflow (Onboarding Cheat Sheet)
1. **Model updates**  
   Edit SQLAlchemy models under `app/models/` and, when needed, update response schemas under `app/schemas/`.
2. **Generate a migration**  
   ```bash
   alembic revision --autogenerate -m "describe change"
   ```
   Review the generated file in `alembic/versions/` to confirm it matches expectations. Hand-edit when automagic detection misses intent.
3. **Apply the migration locally**  
   ```bash
   alembic upgrade head
   ```
   Run `pytest` to verify behaviour and consider seeding your local database if new data is required.
4. **Promotion**  
   Commit the migration alongside model/schema updates. In CI/CD or production deploys, run `alembic upgrade head` (the Docker instructions below include a suitable command).

## Redis Queue Stub
`app/services/task_queue.py` wraps a simple Redis list. It demonstrates how to fan out user events (`user.created`) for future workers. Replace or extend this stub with a real worker process when requirements arrive.

## Docker & Compose
- `backend/Dockerfile` builds a production-ready image. It installs the package and exposes Uvicorn on port 8000.
- `deploy/docker-compose.yaml` provides a development stack (API + Postgres + Redis). By default it loads environment values from `backend/.env.example`. Create `backend/.env` to override without touching version-controlled files:
  ```bash
  cp backend/.env.example backend/.env
  docker compose -f deploy/docker-compose.yaml --env-file backend/.env up --build
  ```
- Run migrations in a container:
  ```bash
  docker compose -f deploy/docker-compose.yaml run --rm backend alembic upgrade head
  ```

## Project Layout
```
backend/
├── app/
│   ├── api/            # FastAPI routers and dependencies
│   ├── core/           # Settings and configuration
│   ├── db/             # SQLAlchemy engine/session utilities
│   ├── models/         # Database models (expand here)
│   ├── schemas/        # Pydantic response/request models
│   └── services/       # Infrastructure services (Redis queue, etc.)
├── alembic/            # Migration environment and scripts
├── alembic.ini
├── Dockerfile
├── Makefile
├── pyproject.toml
└── tests/
```

## API Smoke Test
Once the app is running and migrations applied:
```bash
curl http://localhost:8000/api/v1/health
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","full_name":"Demo User"}'
```

The second call should respond with the created user and a UUID. Check Redis (`redis-cli LRANGE tasks 0 -1`) to see the enqueued background event.
