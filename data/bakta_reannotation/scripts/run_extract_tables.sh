#!/bin/bash
# Extract bakta annotation tables from all JSON files sequentially.
# 176 NERSC chunks (500k seqs each) + 9 CTS chunks (5M seqs each)
#
# Usage: nohup bash run_extract_tables.sh > extract_tables.log 2>&1 &
#
# Estimated time: ~3.5 hours (45s per NERSC chunk, ~7.5 min per CTS chunk)

set -e

WORK_DIR=/pscratch/sd/p/psdehal/bakta_reannotation
SCRIPT_DIR=/global/u2/p/psdehal/BERIL-research-observatory/data/bakta_reannotation/scripts
PYTHON=/global/homes/p/psdehal/.conda/envs/bakta/bin/python3

COMPLETED=0
FAILED=0
START_TIME=$(date +%s)

run_chunk() {
    local json_file=$1
    local out_dir=$2
    local label=$3

    if [ ! -f "${json_file}" ]; then
        echo "SKIP: ${json_file} not found"
        FAILED=$((FAILED + 1))
        return
    fi

    echo "=== [$(date '+%H:%M:%S')] ${label}: ${json_file} ==="
    mkdir -p "${out_dir}"
    if ${PYTHON} "${SCRIPT_DIR}/extract_bakta_tables.py" "${json_file}" "${out_dir}"; then
        COMPLETED=$((COMPLETED + 1))
    else
        echo "FAILED: ${label}"
        FAILED=$((FAILED + 1))
    fi
}

# NERSC chunks: 0-175
for i in $(seq 0 175); do
    CHUNK_NUM=$(printf "%03d" $i)
    run_chunk \
        "${WORK_DIR}/results_500k/chunk_${CHUNK_NUM}/chunk_${CHUNK_NUM}.json" \
        "${WORK_DIR}/tables/chunk_${CHUNK_NUM}" \
        "NERSC chunk_${CHUNK_NUM}"
done

# CTS chunks: 000-007, 009
for CHUNK_NUM in 000 001 002 003 004 005 006 007 009; do
    run_chunk \
        "${WORK_DIR}/results_cts/5M_chunk_${CHUNK_NUM}/chunk_${CHUNK_NUM}.json" \
        "${WORK_DIR}/tables/cts_chunk_${CHUNK_NUM}" \
        "CTS chunk_${CHUNK_NUM}"
done

END_TIME=$(date +%s)
ELAPSED=$(( (END_TIME - START_TIME) / 60 ))

echo ""
echo "========================================"
echo "EXTRACTION COMPLETE"
echo "========================================"
echo "Completed: ${COMPLETED}"
echo "Failed:    ${FAILED}"
echo "Elapsed:   ${ELAPSED} minutes"
