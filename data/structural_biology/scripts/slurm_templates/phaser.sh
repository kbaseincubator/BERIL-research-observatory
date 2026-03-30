#!/bin/bash
#SBATCH --qos=regular
#SBATCH --constraint=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=${PHENIX_CPUS:-32}
#SBATCH --time=${PHENIX_TIME:-04:00:00}
#SBATCH --job-name=phenix_phaser_${PHENIX_PROJECT_ID:-unknown}
#SBATCH --output=phenix_phaser_%j.out
#SBATCH --error=phenix_phaser_%j.err
#
# phenix.phaser — Molecular replacement.
#
# Required environment variables:
#   PHENIX_DATA       — Input MTZ reflection data
#   PHENIX_MODEL      — Search model PDB (e.g., AlphaFold or homolog)
#   PHENIX_SEQ        — Sequence FASTA file
#   PHENIX_NCOPIES    — Expected copies in ASU (default: 1)
#   PHENIX_EXTRA      — Additional Phaser arguments
#
# Usage:
#   PHENIX_DATA=data.mtz PHENIX_MODEL=search.pdb PHENIX_SEQ=seq.fa sbatch phaser.sh

set -euo pipefail

module load conda
conda activate phenix

echo "=== phenix.phaser ==="
echo "Date: $(date -Iseconds)"
echo "Node: $(hostname)"
echo "CPUs: ${SLURM_CPUS_PER_TASK}"
echo "Data: ${PHENIX_DATA:?Set PHENIX_DATA}"
echo "Search model: ${PHENIX_MODEL:?Set PHENIX_MODEL}"
echo "Sequence: ${PHENIX_SEQ:?Set PHENIX_SEQ}"
echo ""

NCOPIES="${PHENIX_NCOPIES:-1}"

phenix.phaser \
    hklin="${PHENIX_DATA}" \
    model="${PHENIX_MODEL}" \
    seq_file="${PHENIX_SEQ}" \
    component_copies="${NCOPIES}" \
    nproc="${SLURM_CPUS_PER_TASK}" \
    ${PHENIX_EXTRA:-}

echo ""
echo "=== Done: $(date -Iseconds) ==="
