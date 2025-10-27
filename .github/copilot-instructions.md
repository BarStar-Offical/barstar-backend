# GitHub Copilot Instructions for Barstar Backend

## Project Overview
This is a FastAPI service backed by PostgreSQL, Redis, and Alembic migrations. The goal is to keep the foundation simple while providing enough structure for a productive developer experience.

## Tech Stack
- **Framework**: FastAPI + Uvicorn for the HTTP API
- **Database**: SQLAlchemy 2.0 ORM with PostgreSQL
- **Migrations**: Alembic
- **Cache/Queue**: Redis for task queue
- **Package Management**: Hatch (PEP 621) managed with `uv`
- **Tooling**: Ruff, Black, MyPy, and Pytest
- **Python Version**: 3.11+

## Project Structure
```
app/
├── api/            # FastAPI routers and dependencies
├── core/           # Settings and configuration
├── db/             # SQLAlchemy engine/session utilities
├── models/         # Database models (expand here)
├── schemas/        # Pydantic response/request models
└── services/       # Infrastructure services (Redis queue, etc.)
alembic/            # Migration environment and scripts
tests/              # Test suite
```

## Code Style & Conventions

### General Guidelines
- Follow PEP 8 and PEP 621 conventions
- Use type hints for all function signatures (enforced by MyPy strict mode)
- Line length: 100 characters (configured in Ruff and Black)
- Target Python version: 3.14 (as configured in pyproject.toml)

### Naming Conventions
- **Files**: Use snake_case (e.g., `user_service.py`)
- **Classes**: Use PascalCase (e.g., `UserModel`, `UserSchema`)
- **Functions/Variables**: Use snake_case (e.g., `create_user`, `user_id`)
- **Constants**: Use UPPER_SNAKE_CASE (e.g., `MAX_RETRY_COUNT`)

### Import Ordering
- Use Ruff to automatically organize imports
- Imports should be grouped: standard library, third-party, local
- Use `from __future__ import annotations` for forward references

### Documentation
- Use docstrings for modules, classes, and public functions
- Follow Google-style or NumPy-style docstrings
- Keep inline comments minimal and meaningful

## Development Workflow

### Making Code Changes
1. **Always format code**: Run `make fmt` before committing
2. **Always lint code**: Run `make lint` to catch issues
3. **Always test changes**: Run `make test` to verify behavior
4. **Document changes**: Update relevant README.md files when changing workflows

### Working with Models
1. Update SQLAlchemy models under `app/models/`
2. Update corresponding Pydantic schemas under `app/schemas/`
3. Generate migration: `alembic revision --autogenerate -m "describe change"`
4. Review generated migration in `alembic/versions/`
5. Apply migration: `alembic upgrade head`
6. Run tests to verify behavior

### API Development
- All API routes should be organized in `app/api/`
- Use FastAPI dependency injection for database sessions
- Document API endpoints using FastAPI's built-in documentation
- Return appropriate Pydantic schemas for type safety
- Follow RESTful conventions for endpoint design

### Testing
- Write tests in the `tests/` directory
- Use `pytest` with async support (`pytest-asyncio`)
- Test database operations with appropriate fixtures
- Aim for meaningful test coverage, not just coverage percentage

### Error Handling
- Use FastAPI's HTTPException for API errors
- Log errors using structlog for structured logging
- Provide meaningful error messages to clients
- Use appropriate HTTP status codes

## Database & Migrations

### Alembic Usage
- **Generate migration**: `alembic revision --autogenerate -m "description"`
- **Apply migrations**: `make migrations-up` or `alembic upgrade head`
- **Rollback one migration**: `make migrations-down` or `alembic downgrade -1`
- **Reset database**: `make db-reset` (downgrade to base, then upgrade to head)
- **Seed database**: `make db-seed`

### Model Conventions
- Use SQLAlchemy 2.0 syntax (declarative base with type annotations)
- Include `created_at` and `updated_at` timestamps where appropriate
- Use UUIDs for primary keys when possible
- Define proper relationships with `relationship()` and `back_populates`
- Use appropriate column types (e.g., `CITEXT` for case-insensitive emails)

## Redis & Background Tasks
- Redis is used for a simple task queue (see `app/services/task_queue.py`)
- Enqueue events like `user.created` for future worker processing
- This is a stub implementation; extend as requirements arrive

## Docker & Deployment
- `Dockerfile` builds production-ready images
- `deploy/docker-compose.yaml` provides development stack
- Use `.env` for local configuration (copy from `.env.example`)
- Migrations should run before starting the API in production

## Environment Variables
- Copy `.env.example` to `.env` for local development
- Use `pydantic-settings` for configuration management
- Access settings via `app.core.config.get_settings()`
- Never commit `.env` or secrets to version control

## Common Commands
- `make install-dev`: Install dependencies including dev tools
- `make fmt`: Format code with Ruff and Black
- `make lint`: Run static analysis with Ruff and MyPy
- `make test`: Run pytest suite
- `make migrations-up`: Apply database migrations
- `make migrations-down`: Rollback one migration
- `make db-reset`: Reset database to head
- `make db-seed`: Populate database with seed data

## Best Practices

### Security
- Never commit secrets or API keys
- Use environment variables for sensitive configuration
- Validate and sanitize all user inputs
- Use parameterized queries (SQLAlchemy handles this)

### Performance
- Use async/await for I/O operations
- Optimize database queries (use `select()` with joins when needed)
- Consider Redis caching for frequently accessed data
- Use connection pooling (configured in SQLAlchemy)

### Maintainability
- Keep functions small and focused (single responsibility)
- Write self-documenting code with clear variable names
- Add comments only when the code's intent is not obvious
- Regularly update dependencies and address deprecation warnings

## Agent Workflow
When making changes, agents should:
1. Document significant workflow changes in appropriate README.md files
2. Update API route documentation when routes are added/removed
3. Fix inconsistencies or outdated information in documentation
4. Add a summary of significant changes to `agent-log.md` with date and timestamp

## Additional Resources
- FastAPI Documentation: https://fastapi.tiangolo.com/
- SQLAlchemy 2.0 Documentation: https://docs.sqlalchemy.org/
- Alembic Documentation: https://alembic.sqlalchemy.org/
- Pydantic Documentation: https://docs.pydantic.dev/
