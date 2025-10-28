#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel || pwd)"
VENV="${REPO_ROOT}/.venv"
PY="${VENV}/bin/python"

if [[ ! -x ${PY} ]]; then
	echo "❌ Virtualenv not found at ${PY}. Run: make install-dev"
	exit 1
fi

# Option A: prepend venv bin to PATH so bare commands work
export PATH="${VENV}/bin:${PATH}"

# Skip interactive prompt in CI or non-interactive environments
if [[ -t 0 ]]; then
	read -rp "Do you want to start the Barstar backend server now? (y/n) " ans
	if [[ "${ans,,}" == "y" || "${ans,,}" == "yes" ]]; then
		echo "🚀 Starting Barstar backend server..."
		cd "${REPO_ROOT}"
		exec docker compose up --build -d
	else
		echo "ℹ️  Skipping backend server startup."
	fi
else
	echo "ℹ️  Non-interactive environment detected. Skipping backend server startup."
fi