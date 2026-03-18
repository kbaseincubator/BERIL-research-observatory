#!/bin/bash
#SBATCH --job-name=iprscan
#SBATCH --account=kbase
#SBATCH --qos=shared
#SBATCH --constraint=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=04:00:00
#SBATCH --output=/pscratch/sd/p/psdehal/interproscan/logs/iprscan_%A_%a.out
#SBATCH --error=/pscratch/sd/p/psdehal/interproscan/logs/iprscan_%A_%a.err
#SBATCH --array=0-4999%500
#
# Production InterProScan on shared queue.
# Each job processes one 10K-sequence FASTA split using 8 CPUs.
#
# Usage:
#   # First batch (splits 0-4999):
#   sbatch --array=0-4999%500 run_iprscan_shared.sh
#
#   # Second batch (splits 5000-9999):
#   sbatch --array=5000-9999%500 run_iprscan_shared.sh
#
#   # Third batch (splits 10000-13253):
#   sbatch --array=10000-13253%500 run_iprscan_shared.sh
#
# %500 limits concurrent running jobs to 500. Adjust as needed.
# Skip logic: completed splits are skipped on resubmission.

set -euo pipefail
module load python

IPRSCAN_HOME=/pscratch/sd/p/psdehal/interproscan/interproscan-5.77-108.0
SPLITS_DIR=/pscratch/sd/p/psdehal/interproscan/splits
RESULTS_DIR=/pscratch/sd/p/psdehal/interproscan/results
NCPU=8

mkdir -p "$RESULTS_DIR"

# ── Resolve input file ──────────────────────────────────────────────
SPLIT_NAME=$(printf "split_%05d" "$SLURM_ARRAY_TASK_ID")
INPUT_FASTA="${SPLITS_DIR}/${SPLIT_NAME}.fasta"
OUTPUT_BASE="${RESULTS_DIR}/${SPLIT_NAME}"
RUN_TEMP="/tmp/iprscan_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"

if [ ! -f "$INPUT_FASTA" ]; then
    echo "No input file: $INPUT_FASTA (past end of splits)"
    exit 0
fi

# Skip if already completed
if [ -f "${OUTPUT_BASE}.tsv" ]; then
    echo "SKIP: ${SPLIT_NAME} already complete ($(wc -l < "${OUTPUT_BASE}.tsv") results)"
    exit 0
fi

mkdir -p "$RUN_TEMP"

N_SEQS=$(grep -c "^>" "$INPUT_FASTA")
echo "============================================"
echo "InterProScan: ${SPLIT_NAME}"
echo "  Node:    $(hostname)"
echo "  CPUs:    $NCPU"
echo "  Input:   $INPUT_FASTA ($N_SEQS sequences)"
echo "  Started: $(date)"
echo "============================================"

START_TIME=$(date +%s)

"$IPRSCAN_HOME/interproscan.sh" \
    -i "$INPUT_FASTA" \
    -f tsv \
    -b "$OUTPUT_BASE" \
    -cpu "$NCPU" \
    -goterms \
    -pa \
    -T "$RUN_TEMP"

EXIT_CODE=$?
ELAPSED=$(( $(date +%s) - START_TIME ))

rm -rf "$RUN_TEMP"

if [ $EXIT_CODE -eq 0 ]; then
    N_RESULTS=$(wc -l < "${OUTPUT_BASE}.tsv" 2>/dev/null || echo 0)
    echo "============================================"
    echo "  Completed: $(date)"
    echo "  Results:   $N_RESULTS lines"
    echo "  Wall time: ${ELAPSED}s ($(python3 -c "print(f'{$ELAPSED/60:.1f}')") min)"
    echo "============================================"
else
    echo "ERROR: InterProScan exited with code $EXIT_CODE after ${ELAPSED}s"
    exit $EXIT_CODE
fi
