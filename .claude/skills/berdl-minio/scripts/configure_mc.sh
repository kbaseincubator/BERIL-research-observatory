#!/usr/bin/env bash
set -euo pipefail

if ! command -v mc >/dev/null 2>&1; then
  echo "MinIO client 'mc' is required but not found in PATH." >&2
  exit 1
fi

ALIAS_NAME="${1:-berdl-minio}"
ENDPOINT_URL="${2:-${MINIO_ENDPOINT_URL:-https://minio.berdl.kbase.us}}"

: "${MINIO_ACCESS_KEY:?Set MINIO_ACCESS_KEY before running this script}"
: "${MINIO_SECRET_KEY:?Set MINIO_SECRET_KEY before running this script}"

mc alias set "${ALIAS_NAME}" "${ENDPOINT_URL}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}"
mc ls "${ALIAS_NAME}"

echo "Configured alias '${ALIAS_NAME}' at '${ENDPOINT_URL}'."
