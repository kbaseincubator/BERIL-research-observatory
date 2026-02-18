#!/usr/bin/env bash
set -euo pipefail

BERDL_PROXY=""
ALIAS_NAME="berdl-minio"
ENDPOINT_URL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --berdl-proxy) BERDL_PROXY=1; shift ;;
    *) if [[ -z "${ALIAS_NAME_SET:-}" ]]; then
         ALIAS_NAME="$1"; ALIAS_NAME_SET=1
       else
         ENDPOINT_URL="$1"
       fi
       shift ;;
  esac
done

ENDPOINT_URL="${ENDPOINT_URL:-${MINIO_ENDPOINT_URL:-https://minio.berdl.kbase.us}}"

if [[ -n "${BERDL_PROXY}" ]]; then
  export https_proxy="${https_proxy:-http://127.0.0.1:8123}"
  export no_proxy="${no_proxy:-localhost,127.0.0.1}"
fi

if ! command -v mc >/dev/null 2>&1; then
  echo "MinIO client 'mc' is required but not found in PATH." >&2
  exit 1
fi

: "${MINIO_ACCESS_KEY:?Set MINIO_ACCESS_KEY before running this script}"
: "${MINIO_SECRET_KEY:?Set MINIO_SECRET_KEY before running this script}"

mc alias set "${ALIAS_NAME}" "${ENDPOINT_URL}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}"
mc ls "${ALIAS_NAME}"

echo "Configured alias '${ALIAS_NAME}' at '${ENDPOINT_URL}'."
if [[ -n "${BERDL_PROXY}" ]]; then
  echo "Using proxy: ${https_proxy}"
fi
