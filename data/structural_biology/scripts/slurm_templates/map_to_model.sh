#!/bin/bash
#SBATCH --qos=regular
#SBATCH --constraint=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=${PHENIX_CPUS:-32}
#SBATCH --time=${PHENIX_TIME:-24:00:00}
#SBATCH --job-name=phenix_map2model_${PHENIX_PROJECT_ID:-unknown}
#SBATCH --output=phenix_map2model_%j.out
#SBATCH --error=phenix_map2model_%j.err
#
# phenix.map_to_model — Build atomic model into cryo-EM map.
#
# Required environment variables:
#   PHENIX_MAP        — Input map file (MRC/CCP4)
#   PHENIX_SEQ        — Sequence FASTA file
#   PHENIX_RESOLUTION — Map resolution in Angstroms
#   PHENIX_EXTRA      — Additional arguments
#
# Usage:
#   PHENIX_MAP=map.mrc PHENIX_SEQ=seq.fa PHENIX_RESOLUTION=3.0 sbatch map_to_model.sh

set -euo pipefail

module load conda
conda activate phenix

echo "=== phenix.map_to_model ==="
echo "Date: $(date -Iseconds)"
echo "Node: $(hostname)"
echo "CPUs: ${SLURM_CPUS_PER_TASK}"
echo "Map: ${PHENIX_MAP:?Set PHENIX_MAP}"
echo "Sequence: ${PHENIX_SEQ:?Set PHENIX_SEQ}"
echo "Resolution: ${PHENIX_RESOLUTION:?Set PHENIX_RESOLUTION}"
echo ""

phenix.map_to_model \
    "${PHENIX_MAP}" \
    seq_file="${PHENIX_SEQ}" \
    resolution="${PHENIX_RESOLUTION}" \
    nproc="${SLURM_CPUS_PER_TASK}" \
    ${PHENIX_EXTRA:-}

echo ""
echo "=== Done: $(date -Iseconds) ==="
