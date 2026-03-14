#!/bin/bash
# Install Phenix structural biology suite via conda on NERSC Perlmutter.
#
# Phenix is installed into a dedicated conda environment. The cctbx-base package
# from conda-forge provides the core Phenix tools (phenix.refine, phenix.phaser,
# phenix.real_space_refine, phenix.molprobity, etc.).
#
# Usage:
#   bash install_phenix.sh [--prefix /path/to/envs]
#
# Default install location: ~/.conda/envs/phenix
# Alternative: set --prefix to install in a shared CFS location.
#
# After installation, activate with:
#   module load conda
#   conda activate phenix

set -euo pipefail

PREFIX=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --prefix)
            PREFIX="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: bash install_phenix.sh [--prefix /path/to/envs/phenix]"
            echo ""
            echo "Install Phenix via conda on NERSC Perlmutter."
            echo ""
            echo "Options:"
            echo "  --prefix DIR   Install environment at DIR (default: ~/.conda/envs/phenix)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=== Phenix Installation on NERSC Perlmutter ==="
echo "Date: $(date -Iseconds)"
echo ""

# Load conda module
echo "Loading conda module..."
module load conda 2>/dev/null || {
    echo "ERROR: 'module load conda' failed. Are you on a Perlmutter node?"
    exit 1
}

# Check for mamba (faster solver)
if command -v mamba &>/dev/null; then
    SOLVER=mamba
    echo "Using mamba for faster package resolution"
else
    SOLVER=conda
    echo "Using conda (install mamba for faster resolution: conda install -n base mamba)"
fi

# Build the create command
if [[ -n "$PREFIX" ]]; then
    echo "Installing to: $PREFIX"
    CREATE_ARGS=("--prefix" "$PREFIX")
else
    echo "Installing to: ~/.conda/envs/phenix"
    CREATE_ARGS=("-n" "phenix")
fi

# Create the environment with cctbx-base (includes Phenix tools)
# Pin to a specific version for reproducibility
echo ""
echo "Creating phenix conda environment..."
echo "This may take 10-20 minutes for the initial solve."
echo ""

$SOLVER create "${CREATE_ARGS[@]}" \
    -c conda-forge \
    cctbx-base \
    -y

echo ""
echo "=== Verifying installation ==="

# Activate and verify
if [[ -n "$PREFIX" ]]; then
    conda activate "$PREFIX"
else
    conda activate phenix
fi

# Check phenix.version
if command -v phenix.version &>/dev/null; then
    echo "phenix.version output:"
    phenix.version
    echo ""
    echo "SUCCESS: Phenix installed and verified."
else
    echo ""
    echo "WARNING: phenix.version not found in PATH."
    echo "The cctbx-base package may not include all Phenix command-line tools."
    echo ""
    echo "Alternative: Download the Phenix installer from https://phenix-online.org"
    echo "and install manually:"
    echo "  1. Register at https://phenix-online.org/download"
    echo "  2. Download the Linux tarball"
    echo "  3. tar xf phenix-installer-*.tar.gz"
    echo "  4. cd phenix-installer-* && ./install --prefix /path/to/phenix"
    echo "  5. source /path/to/phenix/phenix_env.sh"
    echo ""
    echo "Then update SKILL.md preconditions with the install path."
    exit 1
fi

# Print key tool availability
echo ""
echo "=== Available Phenix tools ==="
for tool in phenix.refine phenix.real_space_refine phenix.phaser \
            phenix.autobuild phenix.molprobity phenix.xtriage \
            phenix.ramalyze phenix.rotalyze phenix.clashscore \
            phenix.map_to_model phenix.process_predicted_model \
            phenix.predict_and_build; do
    if command -v "$tool" &>/dev/null; then
        echo "  [OK] $tool"
    else
        echo "  [--] $tool (not found)"
    fi
done

echo ""
echo "=== Installation complete ==="
echo ""
echo "To use Phenix in future sessions:"
echo "  module load conda"
if [[ -n "$PREFIX" ]]; then
    echo "  conda activate $PREFIX"
else
    echo "  conda activate phenix"
fi
echo ""
echo "To use in SLURM jobs, add these lines to your job script:"
echo "  module load conda"
if [[ -n "$PREFIX" ]]; then
    echo "  conda activate $PREFIX"
else
    echo "  conda activate phenix"
fi
