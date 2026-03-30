#!/bin/bash
#SBATCH --job-name=iprscan
#SBATCH --qos=regular
#SBATCH --constraint=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --time=02:00:00
#SBATCH --output=logs/iprscan_%A_%a.out
#SBATCH --error=logs/iprscan_%A_%a.err
#SBATCH --array=0-499%50
#
# InterProScan job array for NERSC Perlmutter (CPU partition)
#
# Runs InterProScan on 10K-sequence FASTA sub-chunks with the built-in
# pre-calculated match lookup service enabled (default). Cache hits resolve
# in milliseconds; only true misses run the full analysis (~30-60s each).
#
# Prerequisites:
#   1. InterProScan 5.77-108.0 installed at $IPRSCAN_HOME
#   2. FASTA sub-chunks at $SCRATCH/interproscan/splits/
#   3. Output dir at $SCRATCH/interproscan/results/
#   4. Logs dir: mkdir -p logs/
#
# Usage:
#   # First, split the 5M-sequence chunks into 10K sub-chunks:
#   python scripts/split_fasta.py $SCRATCH/interproscan/fasta/ \
#          $SCRATCH/interproscan/splits/ --chunk-size 10000
#
#   # Then submit (adjust --array range to match number of sub-chunks):
#   #   ls $SCRATCH/interproscan/splits/ | wc -l   → gives max array index
#   sbatch --array=0-<N-1>%50 scripts/07_nersc_interproscan.sh
#
# The %50 limits concurrent jobs to 50. Adjust based on queue availability.
# Each job takes ~30-90 min depending on cache hit rate.

set -euo pipefail

# MobiDB (idrpred-cli.py) requires Python ≥ 3.7 (uses re.Match).
# NERSC system python is 3.6 — load the module to get 3.13.
module load python

# ── Configuration ────────────────────────────────────────────────────
IPRSCAN_HOME="${IPRSCAN_HOME:-$SCRATCH/interproscan/interproscan-5.77-108.0}"
SPLITS_DIR="${SPLITS_DIR:-$SCRATCH/interproscan/splits}"
RESULTS_DIR="${RESULTS_DIR:-$SCRATCH/interproscan/results}"
# Use node-local tmpfs (/tmp) — Lustre (pscratch) causes race conditions
# where temp files vanish before InterProScan binaries can read them.
TEMP_DIR="${TEMP_DIR:-/tmp/iprscan_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}}"

# Number of CPU cores for InterProScan
NCPU=${SLURM_CPUS_PER_TASK:-64}

# ── Resolve input file ──────────────────────────────────────────────
# Sub-chunks are named split_NNNNN.fasta (zero-padded)
TASK_ID=$(printf "%05d" ${SLURM_ARRAY_TASK_ID})
INPUT_FASTA="${SPLITS_DIR}/split_${TASK_ID}.fasta"

if [[ ! -f "$INPUT_FASTA" ]]; then
    echo "ERROR: Input file not found: $INPUT_FASTA"
    echo "Task ID: ${SLURM_ARRAY_TASK_ID}, padded: ${TASK_ID}"
    exit 1
fi

N_SEQS=$(grep -c "^>" "$INPUT_FASTA")
echo "============================================"
echo "InterProScan Job ${SLURM_ARRAY_TASK_ID}"
echo "  Input: $INPUT_FASTA ($N_SEQS sequences)"
echo "  CPUs: $NCPU"
echo "  Started: $(date)"
echo "============================================"

# ── Setup ────────────────────────────────────────────────────────────
mkdir -p "$RESULTS_DIR" "$TEMP_DIR"

OUTPUT_BASE="${RESULTS_DIR}/split_${TASK_ID}"

# Skip if already completed
if [[ -f "${OUTPUT_BASE}.tsv" ]]; then
    N_DONE=$(wc -l < "${OUTPUT_BASE}.tsv")
    echo "Output already exists: ${OUTPUT_BASE}.tsv ($N_DONE lines)"
    echo "Skipping (delete to re-run)."
    exit 0
fi

# ── Run InterProScan ─────────────────────────────────────────────────
# Key flags:
#   -i:         input FASTA
#   -f tsv:     tab-separated output (most compact)
#   -cpu:       parallel threads
#   -goterms:   include GO annotations
#   -pa:        include pathway annotations
#   -T:         temp directory (use node-local scratch)
#   (no -dp):   lookup service ENABLED (default) — cache hits skip analysis
#
# The lookup service URL is configured in interproscan.properties.
# Default: http://www.ebi.ac.uk/interpro/match-lookup
# Ensure the version matches (5.77-108.0).

"${IPRSCAN_HOME}/interproscan.sh" \
    -i "$INPUT_FASTA" \
    -f tsv \
    -b "$OUTPUT_BASE" \
    -cpu "$NCPU" \
    -goterms \
    -pa \
    -T "$TEMP_DIR" \
    -verbose

EXIT_CODE=$?

# ── Cleanup ──────────────────────────────────────────────────────────
rm -rf "$TEMP_DIR"

if [[ $EXIT_CODE -eq 0 ]]; then
    N_RESULTS=$(wc -l < "${OUTPUT_BASE}.tsv" 2>/dev/null || echo 0)
    echo "============================================"
    echo "  Completed: $(date)"
    echo "  Output: ${OUTPUT_BASE}.tsv ($N_RESULTS result lines)"
    echo "  Exit code: $EXIT_CODE"
    echo "============================================"
else
    echo "ERROR: InterProScan exited with code $EXIT_CODE"
    exit $EXIT_CODE
fi
