#!/usr/bin/env bash
# Download AlphaFold metadata files from EBI FTP to NERSC pscratch.
#
# Files:
#   accession_ids.csv  (7.9 GB) - UniProt accession, residue range, AF ID, version
#   msa_depths.csv     (3.5 GB) - MSA depth per entry
#
# Usage:
#   bash scripts/download_alphafold_data.sh

set -euo pipefail

OUTDIR="/pscratch/sd/p/psdehal/alphafold_collection"
mkdir -p "$OUTDIR"
cd "$OUTDIR"

echo "=== Downloading AlphaFold metadata to $OUTDIR ==="

# accession_ids.csv (top-level FTP directory)
if [[ -f accession_ids.csv ]]; then
    echo "accession_ids.csv already exists, skipping (delete to re-download)"
else
    echo "Downloading accession_ids.csv (7.9 GB)..."
    wget -c "https://ftp.ebi.ac.uk/pub/databases/alphafold/accession_ids.csv" \
        -O accession_ids.csv
fi

# msa_depths.csv (under latest/)
if [[ -f msa_depths.csv ]]; then
    echo "msa_depths.csv already exists, skipping (delete to re-download)"
else
    echo "Downloading msa_depths.csv (3.5 GB)..."
    wget -c "https://ftp.ebi.ac.uk/pub/databases/alphafold/latest/msa_depths.csv" \
        -O msa_depths.csv
fi

echo ""
echo "=== Download complete ==="
ls -lh "$OUTDIR"/*.csv

echo ""
echo "Row counts:"
wc -l "$OUTDIR"/accession_ids.csv
wc -l "$OUTDIR"/msa_depths.csv
