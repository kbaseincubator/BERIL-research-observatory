#!/usr/bin/env bash
set -euo pipefail

# Installs packages required for local Lakehouse ingest into an existing .venv-berdl.
# Run bootstrap_client.sh first if .venv-berdl does not exist yet.
#
# Usage: bash scripts/bootstrap_ingest.sh [venv_path]

VENV_PATH="${1:-.venv-berdl}"

if [[ ! -d "${VENV_PATH}" ]]; then
  echo "ERROR: ${VENV_PATH} not found. Run bootstrap_client.sh first."
  exit 1
fi

# shellcheck source=/dev/null
source "${VENV_PATH}/bin/activate"

echo "Installing ingest packages into ${VENV_PATH}..."

# notebook execution support (for running ingest notebooks via nbconvert)
python -m pip install jupyter nbconvert

# data_lakehouse_ingest installed with --no-deps because its declared dependencies
# (berdl_notebook_utils, etc.) are JupyterHub-only and unavailable outside the cluster.
# The ingest notebook stubs those modules via sys.modules before importing.
python -m pip install --no-deps \
  "git+https://github.com/kbase/data-lakehouse-ingest.git"

# standard dependencies of data_lakehouse_ingest (PyPI-available)
python -m pip install \
  "minio>=7.2.0" \
  "linkml>=1.9.4" \
  "linkml-runtime>=1.9.5" \
  "linkml-validator>=0.4.5"

echo "Verifying installation..."
python -c "import importlib.util; assert importlib.util.find_spec('data_lakehouse_ingest'), 'data_lakehouse_ingest not found'; print('data_lakehouse_ingest OK')"

echo "Ingest environment is ready."
echo "Also ensure mc is configured: bash scripts/configure_mc.sh --berdl-proxy"
