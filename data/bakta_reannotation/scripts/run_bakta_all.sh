#!/bin/bash
set -eo pipefail

# Sequential CTS runner — one 5M chunk at a time, wait for completion
# Uses the proven run_bakta_simple.sh worker (1 chunk, no parallel)
# Submits jobs ourselves, one by one

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
AUTH_TOKEN=$(grep "KBASE_AUTH_TOKEN" "$REPO_DIR/.env" | cut -d'"' -f2)

TOTAL_CHUNKS=27
START=${1:-0}

# Build DB files list once
DB_FILES=$(mc ls --recursive berdl-minio/cts/io/psdehal/bakta_db_v6_extracted/ 2>&1 | awk '{print "\"cts/io/psdehal/bakta_db_v6_extracted/"$NF"\""}' | paste -sd,)

echo "=== Bakta Sequential Runner ==="
echo "Chunks: $TOTAL_CHUNKS (starting from $START)"
echo "Started: $(date -u)"
echo ""

for IDX in $(seq $START $((TOTAL_CHUNKS - 1))); do
    CHUNK_NAME=$(printf "chunk_%03d" $IDX)
    OUTPUT_DIR="cts/io/psdehal/bakta_reannotation/results/5M_${CHUNK_NAME}"

    # Skip if output already exists
    EXISTING=$(mc ls "berdl-minio/$OUTPUT_DIR/" 2>&1 | grep -c "\.tsv" || true)
    if [ "$EXISTING" -gt 0 ]; then
        echo "[$IDX/$((TOTAL_CHUNKS-1))] $CHUNK_NAME — SKIP (output exists)"
        continue
    fi

    echo "[$IDX/$((TOTAL_CHUNKS-1))] $CHUNK_NAME — submitting..."

    RESULT=$(curl -s -X POST \
      -H "Authorization: Bearer $AUTH_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"cluster\": \"kbase\",
        \"image\": \"ghcr.io/kbasetest/cts_python_test:0.1.0\",
        \"params\": {
          \"args\": [\"/in/run_bakta_simple.sh\", \"/out/\"],
          \"input_mount_point\": \"/in\",
          \"output_mount_point\": \"/out\"
        },
        \"input_files\": [\"cts/io/psdehal/bakta_reannotation/scripts/run_bakta_simple.sh\",$DB_FILES,\"cts/io/psdehal/bakta_reannotation/fasta_chunks_5M/${CHUNK_NAME}.fasta\"],
        \"output_dir\": \"$OUTPUT_DIR\",
        \"num_containers\": 1,
        \"cpus\": 168,
        \"memory\": \"900GB\",
        \"runtime\": \"PT2H55M\"
      }" \
      https://berdl.kbase.us/apis/cts/jobs 2>&1)

    JOB_ID=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('job_id',''))" 2>/dev/null)

    if [ -z "$JOB_ID" ]; then
        echo "  SUBMIT FAILED: $RESULT"
        echo "  Retrying in 60s..."
        sleep 60
        continue
    fi

    echo "  Job: $JOB_ID"

    # Poll until complete or error
    while true; do
        sleep 120
        STATE=$(curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
          "https://berdl.kbase.us/apis/cts/jobs/$JOB_ID/status" 2>&1 | \
          python3 -c "import json,sys; print(json.load(sys.stdin).get('state','?'))" 2>/dev/null || echo "?")

        if [ "$STATE" = "complete" ]; then
            echo "  $(date -u '+%H:%M') COMPLETE"
            mc ls "berdl-minio/$OUTPUT_DIR/" 2>&1 | grep "\.tsv"
            echo ""
            break
        elif [ "$STATE" = "error" ] || [ "$STATE" = "canceled" ]; then
            echo "  $(date -u '+%H:%M') $STATE"
            curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
              "https://berdl.kbase.us/apis/cts/jobs/$JOB_ID/log/0/stdout" 2>&1 | tail -10
            curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
              "https://berdl.kbase.us/apis/cts/jobs/$JOB_ID/log/0/stderr" 2>&1 | tail -5
            echo ""
            break
        else
            echo "  $(date -u '+%H:%M') $STATE"
        fi
    done
done

echo "=== All done: $(date -u) ==="
