#!/bin/bash
#SBATCH --qos=regular
#SBATCH --constraint=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=${PHENIX_CPUS:-8}
#SBATCH --time=${PHENIX_TIME:-04:00:00}
#SBATCH --job-name=phenix_refine_${PHENIX_PROJECT_ID:-unknown}
#SBATCH --output=phenix_refine_%j.out
#SBATCH --error=phenix_refine_%j.err
#
# phenix.refine — Reciprocal-space refinement for X-ray crystallography.
#
# Required environment variables or CLI arguments:
#   PHENIX_MODEL     — Input PDB model
#   PHENIX_DATA      — Input MTZ reflection data
#   PHENIX_STRATEGY  — Refinement strategy (default: individual_sites+individual_adp)
#   PHENIX_CYCLES    — Number of macro cycles (default: 5)
#   PHENIX_EXTRA     — Additional phenix.refine arguments
#
# Usage:
#   PHENIX_MODEL=model.pdb PHENIX_DATA=data.mtz sbatch refine.sh
#   PHENIX_MODEL=model.pdb PHENIX_DATA=data.mtz PHENIX_STRATEGY="individual_sites+individual_adp+tls" sbatch refine.sh

set -euo pipefail

# Activate Phenix
module load conda
conda activate phenix

echo "=== phenix.refine ==="
echo "Date: $(date -Iseconds)"
echo "Node: $(hostname)"
echo "CPUs: ${SLURM_CPUS_PER_TASK}"
echo "Model: ${PHENIX_MODEL:?Set PHENIX_MODEL}"
echo "Data: ${PHENIX_DATA:?Set PHENIX_DATA}"
echo ""

STRATEGY="${PHENIX_STRATEGY:-individual_sites+individual_adp}"
CYCLES="${PHENIX_CYCLES:-5}"

phenix.refine \
    "${PHENIX_DATA}" \
    "${PHENIX_MODEL}" \
    refinement.refine.strategy="${STRATEGY}" \
    main.number_of_macro_cycles="${CYCLES}" \
    nproc="${SLURM_CPUS_PER_TASK}" \
    ${PHENIX_EXTRA:-}

echo ""
echo "=== Done: $(date -Iseconds) ==="
