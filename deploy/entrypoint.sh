#!/usr/bin/env bash
set -euo pipefail

APP_MODULE=${UVICORN_APP:-app.main:app}
HOST=${UVICORN_HOST:-0.0.0.0}
PORT=${UVICORN_PORT:-8000}
RELOAD=${UVICORN_RELOAD:-true}

cmd=(uvicorn "${APP_MODULE}" --host "${HOST}" --port "${PORT}")

if [[ ${RELOAD,,} == "true" ]]; then
	export WATCHFILES_FORCE_POLLING="${WATCHFILES_FORCE_POLLING:-true}"
	cmd+=(--reload --reload-dir /app)
fi

exec "${cmd[@]}"
