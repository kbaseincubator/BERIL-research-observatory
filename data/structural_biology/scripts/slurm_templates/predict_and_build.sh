#!/bin/bash
#SBATCH --qos=regular
#SBATCH --constraint=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=${PHENIX_CPUS:-32}
#SBATCH --time=${PHENIX_TIME:-48:00:00}
#SBATCH --job-name=phenix_pab_${PHENIX_PROJECT_ID:-unknown}
#SBATCH --output=phenix_pab_%j.out
#SBATCH --error=phenix_pab_%j.err
#
# phenix.predict_and_build — AlphaFold-guided model building.
# Uses AlphaFold predictions to build into experimental maps.
# This is the longest-running Phenix tool (up to 48h).
#
# Required environment variables:
#   PHENIX_MODEL      — AlphaFold predicted model PDB
#   PHENIX_MAP        — Experimental map (MRC/CCP4) for cryo-EM
#   PHENIX_DATA       — MTZ reflection data for X-ray (use MAP or DATA, not both)
#   PHENIX_SEQ        — Sequence FASTA file
#   PHENIX_RESOLUTION — Map resolution in Angstroms
#   PHENIX_EXTRA      — Additional arguments
#
# Usage (cryo-EM):
#   PHENIX_MODEL=af_model.pdb PHENIX_MAP=map.mrc PHENIX_SEQ=seq.fa \
#     PHENIX_RESOLUTION=3.0 sbatch predict_and_build.sh
#
# Usage (X-ray):
#   PHENIX_MODEL=af_model.pdb PHENIX_DATA=data.mtz PHENIX_SEQ=seq.fa \
#     PHENIX_RESOLUTION=2.5 sbatch predict_and_build.sh

set -euo pipefail

module load conda
conda activate phenix

echo "=== phenix.predict_and_build ==="
echo "Date: $(date -Iseconds)"
echo "Node: $(hostname)"
echo "CPUs: ${SLURM_CPUS_PER_TASK}"
echo "Model: ${PHENIX_MODEL:?Set PHENIX_MODEL}"
echo "Sequence: ${PHENIX_SEQ:?Set PHENIX_SEQ}"
echo "Resolution: ${PHENIX_RESOLUTION:?Set PHENIX_RESOLUTION}"
echo ""

# Build command — use map or data depending on what's provided
CMD="phenix.predict_and_build model_file=${PHENIX_MODEL} seq_file=${PHENIX_SEQ} resolution=${PHENIX_RESOLUTION}"

if [[ -n "${PHENIX_MAP:-}" ]]; then
    echo "Map: ${PHENIX_MAP}"
    CMD="${CMD} map_file=${PHENIX_MAP}"
elif [[ -n "${PHENIX_DATA:-}" ]]; then
    echo "Data: ${PHENIX_DATA}"
    CMD="${CMD} data_file=${PHENIX_DATA}"
else
    echo "ERROR: Set PHENIX_MAP (cryo-EM) or PHENIX_DATA (X-ray)"
    exit 1
fi

CMD="${CMD} nproc=${SLURM_CPUS_PER_TASK} ${PHENIX_EXTRA:-}"

echo "Command: ${CMD}"
echo ""
eval "${CMD}"

echo ""
echo "=== Done: $(date -Iseconds) ==="
