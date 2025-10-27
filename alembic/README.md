# Starting from scratch in new devcontainers
```bash
alembic revision --autogenerate -m "initial schema"
make db-seed
alembic upgrade head

Don't keep making additional migrations until we actually ship the initial database schema.
basically, we want to avoid having a long chain of migrations that represent the initial state of the database.
After shipping the initial schema, future changes will be incremental and easier to manage. using alembic revision --autogenerate for those future changes will be fine. So for development, we can just reset the database to zero and regenerate the initial migration when making schema changes before shipping.
```bash
make db-reset
make db-init
make db-seed
```