#!/bin/bash
set -eo pipefail

# Submit all FASTA chunks to CTS for Bakta annotation
#
# Prerequisites:
#   1. extract_cluster_reps.py has completed → fasta_chunks/chunk_NNN.fasta
#   2. Bakta DB tarball staged on MinIO at cts/io/psdehal/bakta_db_v6_full/db.tar.xz
#   3. KBASE_AUTH_TOKEN in .env
#
# Usage: bash submit_all_chunks.sh [--dry-run]
#
# Outputs:
#   - Uploads chunks + worker script to MinIO
#   - Submits one CTS job per chunk
#   - Writes job_manifest.json with all job IDs for monitoring

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
CHUNK_DIR="$SCRIPT_DIR/../fasta_chunks"
MANIFEST="$SCRIPT_DIR/../extraction_manifest.json"
JOB_MANIFEST="$SCRIPT_DIR/../job_manifest.json"
WORKER_SCRIPT="$SCRIPT_DIR/run_bakta_chunk.sh"

DRY_RUN=false
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN=true
    echo "=== DRY RUN ==="
fi

# Load auth token
AUTH_TOKEN=$(grep "KBASE_AUTH_TOKEN" "$REPO_DIR/.env" | cut -d'"' -f2)
if [ -z "$AUTH_TOKEN" ]; then
    echo "ERROR: KBASE_AUTH_TOKEN not found in .env"
    exit 1
fi

# Check prerequisites
if [ ! -f "$MANIFEST" ]; then
    echo "ERROR: extraction_manifest.json not found. Run extract_cluster_reps.py first."
    exit 1
fi

N_CHUNKS=$(python3 -c "import json; print(json.load(open('$MANIFEST'))['n_chunks'])")
echo "=== Bakta CTS Submission ==="
echo "Chunks: $N_CHUNKS"
echo "Worker: $WORKER_SCRIPT"
echo ""

# Upload worker script to MinIO (once)
echo "Uploading worker script..."
if [ "$DRY_RUN" = false ]; then
    mc cp --checksum crc64nvme "$WORKER_SCRIPT" \
        berdl-minio/cts/io/psdehal/bakta_reannotation/scripts/run_bakta_chunk.sh
fi

# Upload all chunks to MinIO
echo "Uploading FASTA chunks to MinIO..."
for CHUNK_FILE in "$CHUNK_DIR"/chunk_*.fasta; do
    CHUNK_NAME=$(basename "$CHUNK_FILE")
    echo "  $CHUNK_NAME ($(du -h "$CHUNK_FILE" | cut -f1))"
    if [ "$DRY_RUN" = false ]; then
        # Check if already uploaded
        mc stat "berdl-minio/cts/io/psdehal/bakta_reannotation/chunks/$CHUNK_NAME" > /dev/null 2>&1 && {
            echo "    (already uploaded, skipping)"
            continue
        }
        mc cp --checksum crc64nvme "$CHUNK_FILE" \
            "berdl-minio/cts/io/psdehal/bakta_reannotation/chunks/$CHUNK_NAME"
    fi
done

# Submit CTS jobs
echo ""
echo "Submitting CTS jobs..."
JOB_IDS="["
FIRST=true

for CHUNK_FILE in "$CHUNK_DIR"/chunk_*.fasta; do
    CHUNK_NAME=$(basename "$CHUNK_FILE" .fasta)

    if [ "$DRY_RUN" = true ]; then
        echo "  Would submit: $CHUNK_NAME"
        continue
    fi

    RESULT=$(curl -s -X POST \
      -H "Authorization: Bearer $AUTH_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"cluster\": \"kbase\",
        \"image\": \"ghcr.io/kbasetest/cts_python_test:0.1.0\",
        \"params\": {
          \"args\": [
            \"/in/run_bakta_chunk.sh\",
            \"/out/\",
            \"/in/$CHUNK_NAME.fasta\"
          ],
          \"input_mount_point\": \"/in\",
          \"output_mount_point\": \"/out\"
        },
        \"input_files\": [
          \"cts/io/psdehal/bakta_reannotation/scripts/run_bakta_chunk.sh\",
          \"cts/io/psdehal/bakta_reannotation/chunks/$CHUNK_NAME.fasta\",
          \"cts/io/psdehal/bakta_db_v6_full/db.tar.xz\"
        ],
        \"output_dir\": \"cts/io/psdehal/bakta_reannotation/output/$CHUNK_NAME\",
        \"num_containers\": 1,
        \"cpus\": 8,
        \"memory\": \"32GB\",
        \"runtime\": \"PT3H\"
      }" \
      https://berdl.kbase.us/apis/cts/jobs 2>&1)

    JOB_ID=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('job_id','ERROR'))" 2>/dev/null || echo "ERROR")

    if [ "$JOB_ID" = "ERROR" ]; then
        echo "  ERROR submitting $CHUNK_NAME: $RESULT"
    else
        echo "  $CHUNK_NAME → $JOB_ID"
        if [ "$FIRST" = true ]; then
            FIRST=false
        else
            JOB_IDS="$JOB_IDS,"
        fi
        JOB_IDS="$JOB_IDS{\"chunk\":\"$CHUNK_NAME\",\"job_id\":\"$JOB_ID\"}"
    fi

    # Small delay between submissions to not overwhelm the API
    sleep 2
done

JOB_IDS="$JOB_IDS]"

# Write job manifest
if [ "$DRY_RUN" = false ]; then
    echo "$JOB_IDS" | python3 -c "
import json, sys
jobs = json.load(sys.stdin)
manifest = {
    'submitted_at': '$(date -u -Iseconds)',
    'n_jobs': len(jobs),
    'jobs': jobs
}
print(json.dumps(manifest, indent=2))
" > "$JOB_MANIFEST"
    echo ""
    echo "=== Submitted $N_CHUNKS jobs ==="
    echo "Job manifest: $JOB_MANIFEST"
else
    echo ""
    echo "=== DRY RUN: Would submit $N_CHUNKS jobs ==="
fi
