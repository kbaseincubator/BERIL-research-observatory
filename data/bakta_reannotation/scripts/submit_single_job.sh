#!/bin/bash
set -eo pipefail

# Submit a single CTS job that processes ALL chunks in parallel
#
# Prerequisites:
#   1. extract_cluster_reps.py has completed → fasta_chunks/chunk_NNN.fasta
#   2. Bakta DB tarball on MinIO: cts/io/psdehal/bakta_db_v6_full/db.tar.xz
#   3. KBASE_AUTH_TOKEN in .env
#
# Usage: bash submit_single_job.sh [--dry-run]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
CHUNK_DIR="$SCRIPT_DIR/../fasta_chunks"
MANIFEST="$SCRIPT_DIR/../extraction_manifest.json"
WORKER_SCRIPT="$SCRIPT_DIR/run_bakta_all.sh"

DRY_RUN=false
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN=true
    echo "=== DRY RUN ==="
fi

AUTH_TOKEN=$(grep "KBASE_AUTH_TOKEN" "$REPO_DIR/.env" | cut -d'"' -f2)
if [ -z "$AUTH_TOKEN" ]; then
    echo "ERROR: KBASE_AUTH_TOKEN not found in .env"
    exit 1
fi

# Check extraction complete
if [ ! -f "$MANIFEST" ]; then
    echo "ERROR: extraction_manifest.json not found. Run extract_cluster_reps.py first."
    exit 1
fi

N_CHUNKS=$(ls "$CHUNK_DIR"/chunk_*.fasta 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh "$CHUNK_DIR" | cut -f1)
echo "=== Bakta Single-Job Submission ==="
echo "Chunks: $N_CHUNKS ($TOTAL_SIZE)"
echo ""

# Step 1: Tar all chunks into one file (no compression — they're text, tar is fast)
CHUNKS_TAR="$SCRIPT_DIR/../chunks.tar"
if [ -f "$CHUNKS_TAR" ]; then
    echo "chunks.tar already exists ($(du -h "$CHUNKS_TAR" | cut -f1))"
else
    echo "Creating chunks.tar from $N_CHUNKS FASTA files..."
    tar cf "$CHUNKS_TAR" -C "$CHUNK_DIR" .
    echo "Created: $(du -h "$CHUNKS_TAR" | cut -f1)"
fi

# Step 2: Upload worker script + chunks tarball to MinIO
echo ""
echo "Uploading to MinIO..."
if [ "$DRY_RUN" = false ]; then
    echo "  run_bakta_all.sh"
    mc cp --checksum crc64nvme "$WORKER_SCRIPT" \
        berdl-minio/cts/io/psdehal/bakta_reannotation/scripts/run_bakta_all.sh

    echo "  chunks.tar ($(du -h "$CHUNKS_TAR" | cut -f1))"
    mc cp --checksum crc64nvme "$CHUNKS_TAR" \
        berdl-minio/cts/io/psdehal/bakta_reannotation/chunks.tar
fi

# Step 3: Submit single CTS job
echo ""
echo "Submitting CTS job..."
if [ "$DRY_RUN" = true ]; then
    echo "  Would submit: 1 job with $N_CHUNKS chunks"
    echo "  Input: script + chunks.tar + db.tar.xz"
    echo "  CPUs: 168, Memory: 900GB, Runtime: 6h"
    exit 0
fi

RESULT=$(curl -s -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cluster": "kbase",
    "image": "ghcr.io/kbasetest/cts_python_test:0.1.0",
    "params": {
      "args": [
        "/in/run_bakta_all.sh",
        "/out/"
      ],
      "input_mount_point": "/in",
      "output_mount_point": "/out"
    },
    "input_files": [
      "cts/io/psdehal/bakta_reannotation/scripts/run_bakta_all.sh",
      "cts/io/psdehal/bakta_reannotation/chunks.tar",
      "cts/io/psdehal/bakta_db_v6_full/db.tar.xz"
    ],
    "output_dir": "cts/io/psdehal/bakta_reannotation/output",
    "num_containers": 1,
    "cpus": 168,
    "memory": "900GB",
    "runtime": "PT6H"
  }' \
  https://berdl.kbase.us/apis/cts/jobs 2>&1)

JOB_ID=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('job_id','ERROR'))" 2>/dev/null || echo "ERROR")

if [ "$JOB_ID" = "ERROR" ]; then
    echo "ERROR: $RESULT"
    exit 1
fi

echo ""
echo "================================================"
echo "  JOB SUBMITTED: $JOB_ID"
echo "================================================"
echo ""
echo "Monitor with:"
echo "  AUTH_TOKEN=\$(grep KBASE_AUTH_TOKEN .env | cut -d'\"' -f2)"
echo "  curl -s -H \"Authorization: Bearer \$AUTH_TOKEN\" \\"
echo "    https://berdl.kbase.us/apis/cts/jobs/$JOB_ID/status"
echo ""
echo "Logs:"
echo "  curl -s -H \"Authorization: Bearer \$AUTH_TOKEN\" \\"
echo "    https://berdl.kbase.us/apis/cts/jobs/$JOB_ID/log/0/stdout"

# Save job ID
echo "{\"job_id\": \"$JOB_ID\", \"submitted_at\": \"$(date -u -Iseconds)\", \"n_chunks\": $N_CHUNKS}" \
    > "$SCRIPT_DIR/../job_manifest.json"
echo ""
echo "Job ID saved to job_manifest.json"
