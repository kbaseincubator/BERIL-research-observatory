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
  "boto3>=1.34.0"

echo "Environment is ready."
echo "Activate with: source ${VENV_PATH}/bin/activate"
