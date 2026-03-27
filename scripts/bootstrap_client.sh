#!/usr/bin/env bash
set -euo pipefail

VENV_PATH="${1:-.venv}"

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv is required but not installed." >&2
  exit 1
fi

uv sync --extra berdl

if [[ "${VENV_PATH}" != ".venv" && "${VENV_PATH}" != "$(pwd)/.venv" ]]; then
  echo "WARNING: custom venv path '${VENV_PATH}' ignored. uv manages the repo at .venv." >&2
fi

uv pip install --python .venv/bin/python \
  "git+https://github.com/BERDataLakehouse/spark_connect_remote.git" \
  "git+https://github.com/BERDataLakehouse/berdl_remote.git"

# Make scripts/ importable so notebooks can do:
#   from get_spark_session import get_spark_session
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
SITE_PACKAGES="$(uv run python -c 'import site; print(site.getsitepackages()[0])')"
echo "${SCRIPTS_DIR}" > "${SITE_PACKAGES}/berdl-scripts.pth"

echo "Environment is ready."
echo "Activate with: source .venv/bin/activate"
