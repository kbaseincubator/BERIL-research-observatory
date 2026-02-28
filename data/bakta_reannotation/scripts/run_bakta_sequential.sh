#!/bin/bash
set -eo pipefail

# Sequential CTS job runner — submits one job at a time, waits for completion
# Each job processes a batch of chunks with all available CPUs
#
# Usage: bash run_bakta_sequential.sh [start_batch]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
AUTH_TOKEN=$(grep "KBASE_AUTH_TOKEN" "$REPO_DIR/.env" | cut -d'"' -f2)

# 67 chunks, 5 per job = 14 jobs (last one gets 2)
CHUNKS_PER_JOB=5
TOTAL_CHUNKS=67
START_BATCH=${1:-0}

# DB files (same for all jobs)
DB_FILES=$(mc ls --recursive berdl-minio/cts/io/psdehal/bakta_db_v6_extracted/ 2>&1 | awk '{print "\"cts/io/psdehal/bakta_db_v6_extracted/"$NF"\""}' | paste -sd,)
SCRIPT='"cts/io/psdehal/bakta_reannotation/scripts/run_bakta_all.sh"'

echo "=== Sequential Bakta Runner ==="
echo "Chunks per job: $CHUNKS_PER_JOB"
echo "Total chunks: $TOTAL_CHUNKS"
echo "Starting from batch: $START_BATCH"
echo ""

BATCH=$START_BATCH
CHUNK_START=$((BATCH * CHUNKS_PER_JOB))

while [ $CHUNK_START -lt $TOTAL_CHUNKS ]; do
    CHUNK_END=$((CHUNK_START + CHUNKS_PER_JOB - 1))
    [ $CHUNK_END -ge $TOTAL_CHUNKS ] && CHUNK_END=$((TOTAL_CHUNKS - 1))
    N_CHUNKS=$((CHUNK_END - CHUNK_START + 1))

    # Build chunk file list
    CHUNK_FILES=""
    for j in $(seq $CHUNK_START $CHUNK_END); do
        CHUNK_FILES="${CHUNK_FILES},\"cts/io/psdehal/bakta_reannotation/fasta_chunks/chunk_$(printf '%03d' $j).fasta\""
    done
    CHUNK_FILES="${CHUNK_FILES:1}"

    INPUT_FILES="[$SCRIPT,$DB_FILES,$CHUNK_FILES]"

    echo "=== Batch $BATCH: chunks $(printf '%03d' $CHUNK_START)-$(printf '%03d' $CHUNK_END) ($N_CHUNKS chunks, ~$((N_CHUNKS * 2))M proteins) ==="
    echo "Submitting at $(date -u)..."

    RESULT=$(curl -s -X POST \
      -H "Authorization: Bearer $AUTH_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"cluster\": \"kbase\",
        \"image\": \"ghcr.io/kbasetest/cts_python_test:0.1.0\",
        \"params\": {
          \"args\": [\"/in/run_bakta_all.sh\", \"/out/\"],
          \"input_mount_point\": \"/in\",
          \"output_mount_point\": \"/out\"
        },
        \"input_files\": $INPUT_FILES,
        \"output_dir\": \"cts/io/psdehal/bakta_reannotation/results/batch_$(printf '%02d' $BATCH)\",
        \"num_containers\": 1,
        \"cpus\": 168,
        \"memory\": \"900GB\",
        \"runtime\": \"PT2H55M\"
      }" \
      https://berdl.kbase.us/apis/cts/jobs 2>&1)

    JOB_ID=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('job_id','ERROR'))" 2>/dev/null)

    if [ "$JOB_ID" = "ERROR" ] || [ -z "$JOB_ID" ]; then
        echo "  SUBMIT FAILED: $RESULT"
        exit 1
    fi

    echo "  Job ID: $JOB_ID"

    # Wait for completion
    while true; do
        sleep 120
        STATE=$(curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
          "https://berdl.kbase.us/apis/cts/jobs/$JOB_ID/status" 2>&1 | \
          python3 -c "import json,sys; print(json.load(sys.stdin)['state'])" 2>/dev/null || echo "?")
        echo "  $(date -u '+%H:%M') — $STATE"

        if [ "$STATE" = "complete" ]; then
            echo "  COMPLETE — checking output..."
            mc ls "berdl-minio/cts/io/psdehal/bakta_reannotation/results/batch_$(printf '%02d' $BATCH)/" 2>&1 | head -10
            echo ""
            break
        elif [ "$STATE" = "error" ] || [ "$STATE" = "canceled" ]; then
            echo "  FAILED ($STATE) — checking logs..."
            curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
              "https://berdl.kbase.us/apis/cts/jobs/$JOB_ID/log/0/stdout" 2>&1 | tail -30
            echo ""
            echo "  Continuing to next batch..."
            break
        fi
    done

    BATCH=$((BATCH + 1))
    CHUNK_START=$((BATCH * CHUNKS_PER_JOB))
done

echo "=== All batches submitted ==="
echo "Finished at $(date -u)"
