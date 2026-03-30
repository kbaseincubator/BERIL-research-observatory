#!/bin/bash
#SBATCH --qos=regular
#SBATCH --constraint=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=${PHENIX_CPUS:-8}
#SBATCH --time=${PHENIX_TIME:-04:00:00}
#SBATCH --job-name=phenix_rsr_${PHENIX_PROJECT_ID:-unknown}
#SBATCH --output=phenix_rsr_%j.out
#SBATCH --error=phenix_rsr_%j.err
#
# phenix.real_space_refine — Real-space refinement against cryo-EM maps.
#
# Required environment variables:
#   PHENIX_MODEL      — Input PDB model
#   PHENIX_MAP        — Input map file (MRC/CCP4)
#   PHENIX_RESOLUTION — Map resolution in Angstroms
#   PHENIX_CYCLES     — Number of macro cycles (default: 5)
#   PHENIX_EXTRA      — Additional arguments
#
# Usage:
#   PHENIX_MODEL=model.pdb PHENIX_MAP=map.mrc PHENIX_RESOLUTION=3.0 sbatch real_space_refine.sh

set -euo pipefail

module load conda
conda activate phenix

echo "=== phenix.real_space_refine ==="
echo "Date: $(date -Iseconds)"
echo "Node: $(hostname)"
echo "CPUs: ${SLURM_CPUS_PER_TASK}"
echo "Model: ${PHENIX_MODEL:?Set PHENIX_MODEL}"
echo "Map: ${PHENIX_MAP:?Set PHENIX_MAP}"
echo "Resolution: ${PHENIX_RESOLUTION:?Set PHENIX_RESOLUTION}"
echo ""

CYCLES="${PHENIX_CYCLES:-5}"

phenix.real_space_refine \
    "${PHENIX_MODEL}" \
    "${PHENIX_MAP}" \
    resolution="${PHENIX_RESOLUTION}" \
    macro_cycles="${CYCLES}" \
    nproc="${SLURM_CPUS_PER_TASK}" \
    ${PHENIX_EXTRA:-}

echo ""
echo "=== Done: $(date -Iseconds) ==="
