#!/bin/bash
#SBATCH --qos=regular
#SBATCH --constraint=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=${PHENIX_CPUS:-32}
#SBATCH --time=${PHENIX_TIME:-08:00:00}
#SBATCH --job-name=phenix_autobuild_${PHENIX_PROJECT_ID:-unknown}
#SBATCH --output=phenix_autobuild_%j.out
#SBATCH --error=phenix_autobuild_%j.err
#
# phenix.autobuild — Automated model building after molecular replacement.
#
# Required environment variables:
#   PHENIX_DATA   — Input MTZ reflection data
#   PHENIX_MODEL  — Input PDB model (from Phaser MR solution)
#   PHENIX_SEQ    — Sequence FASTA file
#   PHENIX_EXTRA  — Additional arguments
#
# Usage:
#   PHENIX_DATA=data.mtz PHENIX_MODEL=phaser_solution.pdb PHENIX_SEQ=seq.fa sbatch autobuild.sh

set -euo pipefail

module load conda
conda activate phenix

echo "=== phenix.autobuild ==="
echo "Date: $(date -Iseconds)"
echo "Node: $(hostname)"
echo "CPUs: ${SLURM_CPUS_PER_TASK}"
echo "Data: ${PHENIX_DATA:?Set PHENIX_DATA}"
echo "Model: ${PHENIX_MODEL:?Set PHENIX_MODEL}"
echo "Sequence: ${PHENIX_SEQ:?Set PHENIX_SEQ}"
echo ""

phenix.autobuild \
    data="${PHENIX_DATA}" \
    model="${PHENIX_MODEL}" \
    seq_file="${PHENIX_SEQ}" \
    nproc="${SLURM_CPUS_PER_TASK}" \
    ${PHENIX_EXTRA:-}

echo ""
echo "=== Done: $(date -Iseconds) ==="
