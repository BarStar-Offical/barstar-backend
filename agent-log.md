# Agent Log

A summary of changes made by the agents during development. All entries should be Dated and timestamped.

- 2025-10-27 00:00 UTC — Added deterministic ordering to operator and venue list endpoints, ensured timestamp defaults fire during SQLite tests, fixed health route prefix, enforced non-null user points in tests, and verified full test suite passes.
- 2025-10-27 08:02 UTC — Set up GitHub Copilot instructions by creating `.github/copilot-instructions.md` with comprehensive repository guidelines, coding conventions, development workflow, and best practices for working with FastAPI, SQLAlchemy, Alembic, and the project structure.
- 2025-10-28 09:30 UTC — Added `CaseInsensitiveText` SQLAlchemy type to wrap PostgreSQL `CITEXT` with a cross-dialect fallback and updated email columns across models to use it.
- 2025-10-28 10:15 UTC — Swapped the SQLite Pytest fixture for a disposable PostgreSQL database (image `ghcr.io/barstar-offical/barstar-postgres-age:16`), introduced the `TEST_DATABASE_URL` env var, and documented the workflow.
