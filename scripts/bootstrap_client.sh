#!/usr/bin/env bash
set -euo pipefail

VENV_PATH="${1:-.venv-berdl}"

if [[ ! -d "${VENV_PATH}" ]]; then
  python3 -m venv "${VENV_PATH}"
fi

# shellcheck source=/dev/null
source "${VENV_PATH}/bin/activate"

python -m pip install --upgrade pip
python -m pip install \
  "git+https://github.com/BERDataLakehouse/spark_connect_remote.git" \
  "git+https://github.com/BERDataLakehouse/berdl_remote.git" \
  "boto3>=1.34.0" \
  "pproxy" \
  "pandas" \
  "matplotlib"

# Make scripts/ importable so notebooks can do:
#   from get_spark_session import get_spark_session
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
SITE_PACKAGES="$(python -c 'import site; print(site.getsitepackages()[0])')"
echo "${SCRIPTS_DIR}" > "${SITE_PACKAGES}/berdl-scripts.pth"

echo "Environment is ready."
echo "Activate with: source ${VENV_PATH}/bin/activate"
