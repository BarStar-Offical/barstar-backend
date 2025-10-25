#!/bin/bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
VENV_PATH="$REPO_ROOT/.venv"
ACTIVATE_SNIPPET="source $VENV_PATH/bin/activate"

cd "$REPO_ROOT"

if [ ! -d "$VENV_PATH" ]; then
	echo "Creating Python virtual environment at $VENV_PATH..."
	python3 -m venv "$VENV_PATH"
	"$VENV_PATH/bin/pip" install --upgrade pip setuptools wheel
	"$VENV_PATH/bin/pip" install -e ".[dev]"
else
	echo "Using existing virtual environment at $VENV_PATH."
fi

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
cd "$REPO_ROOT/deploy"
docker compose up --build -d
echo "Docker compose stack is up (detached). Use 'docker compose logs -f' to follow logs."