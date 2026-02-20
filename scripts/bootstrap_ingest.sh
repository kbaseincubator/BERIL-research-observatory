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

# BERDL internal packages — must use --no-deps because their transitive
# dependencies are JupyterHub-only packages unavailable outside the cluster.
# Install in dependency order: base → utils → ingest.
python -m pip install --no-deps \
  "git+https://github.com/BERDataLakehouse/spark_notebook_base.git" \
  "git+https://github.com/BERDataLakehouse/spark_notebook.git#subdirectory=notebook_utils" \
  "git+https://github.com/kbase/data-lakehouse-ingest.git"

# standard dependencies of data_lakehouse_ingest (PyPI-available)
python -m pip install \
  "minio>=7.2.0" \
  "linkml>=1.9.4" \
  "linkml-runtime>=1.9.5" \
  "linkml-validator>=0.4.5"

echo "Verifying installation..."
python -c "from data_lakehouse_ingest import ingest; print('data_lakehouse_ingest OK')"

echo "Ingest environment is ready."
echo "Also ensure mc is configured: bash scripts/configure_mc.sh --berdl-proxy"
