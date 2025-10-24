#!/bin/bash
set -euo pipefail

echo "Setting up Python virtual environment..."
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"

echo "Python virtual environment is set up and dependencies are installed."
echo "Starting development server..."
alembic upgrade head
uvicorn app.main:app --reload