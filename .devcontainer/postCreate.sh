#!/bin/bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
VENV_PATH="${REPO_ROOT}/.venv"
ACTIVATE_SNIPPET="source ${VENV_PATH}/bin/activate"

# Ensure caches exist and are writable by vscode
mkdir -p /home/vscode/.cache/pip /home/vscode/.cache/uv
sudo chown -R vscode:vscode /home/vscode/.cache

LOCAL_BIN="/home/vscode/.local/bin"
if [ -d "${LOCAL_BIN}" ]; then
	export PATH="${LOCAL_BIN}:${PATH}"
fi

if ! command -v uv >/dev/null 2>&1; then
	curl -LsSf https://astral.sh/uv/install.sh | sh
	if [ -d "${LOCAL_BIN}" ]; then
		export PATH="${LOCAL_BIN}:${PATH}"
	fi
fi

cd "${REPO_ROOT}"
make install-dev

# Auto-activate the environment for future terminals.
if ! grep -Fq "${ACTIVATE_SNIPPET}" /home/vscode/.bashrc; then
	{
		echo ""
		echo "# Auto-activate Barstar backend virtualenv"
		echo "${ACTIVATE_SNIPPET}"
	} >>/home/vscode/.bashrc
	echo "Configured /home/vscode/.bashrc to auto-activate the project virtualenv."
fi
