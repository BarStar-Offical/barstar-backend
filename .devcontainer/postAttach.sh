#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel || pwd)"
VENV="${REPO_ROOT}/.venv"
PY="${VENV}/bin/python"

if [[ ! -x "${PY}" ]]; then
	echo "❌ Virtualenv not found at ${PY}. Run: make install-dev"
	exit 1
fi

# Option A: prepend venv bin to PATH so bare commands work
export PATH="${VENV}/bin:${PATH}"

read -rp "Do you want to start the Barstar backend server now? (y/n) " ans
if [[ ${ans} =~ ^[Yy]$ ]]; then
	echo "Cleaning up any existing docker compose stack..."
	cd "${REPO_ROOT}"
	docker compose down --remove-orphans >/dev/null 2>&1 || true
	echo "Ensuring docker compose services are running..."
	docker compose up --build -d db redis
	echo "Docker compose stack is up (detached). Use 'docker compose logs -f' to follow logs."
	POSTGRES_DB_VALUE=$(grep '^POSTGRES_DB=' .env | cut -d '=' -f2- || true)
	POSTGRES_USER_VALUE=$(grep '^POSTGRES_USER=' .env | cut -d '=' -f2- || true)
	POSTGRES_PASSWORD_VALUE=$(grep '^POSTGRES_PASSWORD=' .env | cut -d '=' -f2- || true)
	POSTGRES_DB_VALUE=${POSTGRES_DB_VALUE:-barstar}
	POSTGRES_USER_VALUE=${POSTGRES_USER_VALUE:-postgres}
	POSTGRES_PASSWORD_VALUE=${POSTGRES_PASSWORD_VALUE:-postgres}
	echo "Waiting for PostgreSQL to become ready..."
	pg_ready=false
	for _ in $(seq 1 30); do
		if docker compose exec db bash -c "export PGPASSWORD='${POSTGRES_PASSWORD_VALUE}'; pg_isready -U '${POSTGRES_USER_VALUE}' -d postgres" >/dev/null 2>&1; then
			pg_ready=true
			break
		fi
		sleep 2
	done
	if [[ "${pg_ready}" != "true" ]]; then
		echo "❌ PostgreSQL did not become ready in time. Showing recent logs:"
		docker compose logs --tail 50 db || true
		exit 1
	fi
	echo "Ensuring target database exists..."
	docker compose exec db bash -c "
    export PGPASSWORD=\"${POSTGRES_PASSWORD_VALUE}\"
    if ! psql -U \"${POSTGRES_USER_VALUE}\" -tAc \"SELECT 1 FROM pg_database WHERE datname = '${POSTGRES_DB_VALUE}'\" | grep -q 1; then
      createdb -U \"${POSTGRES_USER_VALUE}\" \"${POSTGRES_DB_VALUE}\"
    fi
  "
	echo "Applying DB migrations (via backend service container)..."
	docker compose run --rm backend alembic upgrade head

	REDIS_URL_VALUE=$(grep '^REDIS_URL=' .env | cut -d '=' -f2- || true)
	HOST_DATABASE_URL="postgresql+psycopg://${POSTGRES_USER_VALUE}:${POSTGRES_PASSWORD_VALUE}@localhost:5432/${POSTGRES_DB_VALUE}"
	HOST_REDIS_URL=$(
		REDIS_URL_VALUE="${REDIS_URL_VALUE:-redis://redis:6379/0}" python - <<'PY'
from urllib.parse import urlparse, urlunparse
import os

raw = os.environ['REDIS_URL_VALUE']
parts = urlparse(raw)

host = 'localhost'
netloc = host
if parts.port:
  netloc = f"{host}:{parts.port}"

if parts.username or parts.password:
  auth = ''
  if parts.username:
    auth += parts.username
  if parts.password:
    auth += f":{parts.password}"
  netloc = f"{auth}@{netloc}"

print(urlunparse(parts._replace(netloc=netloc)))
PY
	)

	export DATABASE_URL="${HOST_DATABASE_URL}"
	export REDIS_URL="${HOST_REDIS_URL}"

	if pgrep -f "uvicorn .*app\.main" >/dev/null 2>&1; then
		pkill -f "uvicorn .*app\.main" || true
	fi

		echo "Starting Barstar backend server..."
		exec "$PY" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
fi
