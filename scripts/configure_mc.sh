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

# BERDL renamed these from MINIO_* to S3_*. Current name first, historical second,
# so this keeps working on older pod images. Verified on a pod 2026-08-14: only the
# S3_* names exist there.
ENDPOINT_URL="${ENDPOINT_URL:-${S3_ENDPOINT_URL:-${MINIO_ENDPOINT_URL:-https://minio.berdl.kbase.us}}}"
ACCESS_KEY="${S3_ACCESS_KEY:-${MINIO_ACCESS_KEY:-}}"
SECRET_KEY="${S3_SECRET_KEY:-${MINIO_SECRET_KEY:-}}"

if [[ -n "${BERDL_PROXY}" ]]; then
  export https_proxy="${https_proxy:-http://127.0.0.1:8123}"
  export no_proxy="${no_proxy:-localhost,127.0.0.1}"
fi

if ! command -v mc >/dev/null 2>&1; then
  echo "MinIO client 'mc' is required but not found in PATH." >&2
  exit 1
fi

if [[ -z "${ACCESS_KEY}" || -z "${SECRET_KEY}" ]]; then
  echo "No object-store credentials in the environment." >&2
  echo "  Looked for: S3_ACCESS_KEY or MINIO_ACCESS_KEY, and S3_SECRET_KEY or MINIO_SECRET_KEY." >&2
  echo "  On a BERDL pod the current names are S3_*; MINIO_* no longer exists there." >&2
  echo "  Load them with: eval \"\$(python scripts/get_minio_creds.py --shell)\"" >&2
  exit 1
fi

mc alias set "${ALIAS_NAME}" "${ENDPOINT_URL}" "${ACCESS_KEY}" "${SECRET_KEY}"
mc ls "${ALIAS_NAME}"

echo "Configured alias '${ALIAS_NAME}' at '${ENDPOINT_URL}'."
if [[ -n "${BERDL_PROXY}" ]]; then
  echo "Using proxy: ${https_proxy}"
fi
