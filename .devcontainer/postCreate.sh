#!/bin/bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
VENV_PATH="$REPO_ROOT/.venv"
ACTIVATE_SNIPPET="source $VENV_PATH/bin/activate"

# Ensure caches exist and are writable by vscode
mkdir -p /home/vscode/.cache/pip /home/vscode/.cache/uv
sudo chown -R vscode:vscode /home/vscode/.cache

cd "$REPO_ROOT"
make install-dev

# Auto-activate the environment for future terminals.
if ! grep -Fq "$ACTIVATE_SNIPPET" /home/vscode/.bashrc; then
	{
		echo ""
		echo "# Auto-activate Barstar backend virtualenv"
		echo "$ACTIVATE_SNIPPET"
	} >> /home/vscode/.bashrc
	echo "Configured /home/vscode/.bashrc to auto-activate the project virtualenv."
fi

echo "Ensuring docker compose services are running..."
cd "$REPO_ROOT"
docker compose up --build -d
echo "Docker compose stack is up (detached). Use 'docker compose logs -f' to follow logs."