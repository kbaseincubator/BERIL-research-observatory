#!/usr/bin/env bash
set -euo pipefail

# Installs packages required for local Lakehouse ingest into the repo-managed .venv.
# Run bootstrap_client.sh first if .venv does not exist yet.
#
# Usage: bash scripts/bootstrap_ingest.sh [venv_path]

VENV_PATH="${1:-.venv}"

if [[ ! -d "${VENV_PATH}" ]]; then
  echo "ERROR: ${VENV_PATH} not found. Run bootstrap_client.sh first."
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv is required but not installed." >&2
  exit 1
fi

uv sync --extra berdl --extra ingest

echo "Installing ingest packages into ${VENV_PATH}..."

# notebook execution support (for running ingest notebooks via nbconvert)
uv pip install --python .venv/bin/python --no-deps \
  "git+https://github.com/kbase/data-lakehouse-ingest.git"

echo "Verifying installation..."
uv run python -c "import importlib.util; assert importlib.util.find_spec('data_lakehouse_ingest'), 'data_lakehouse_ingest not found'; print('data_lakehouse_ingest OK')"

echo "Ingest environment is ready."
echo "Also ensure mc is configured: bash scripts/configure_mc.sh --berdl-proxy"
