#!/bin/bash
set -eo pipefail

# Simple Bakta worker — processes ONE chunk_*.fasta file from /in/
# DB files are in /in/ as extracted files (symlinked into a directory structure)
# This is the PROVEN script that successfully annotated 1M and 5M protein chunks.

OUTPUT_DIR="$1"

echo "Started: $(date -u)"
echo "CPUs: $(nproc)"

# Install bakta
apt-get update -qq && apt-get install -y -qq wget bzip2 > /dev/null 2>&1
wget -qO /usr/local/bin/micromamba \
  https://github.com/mamba-org/micromamba-releases/releases/latest/download/micromamba-linux-64
chmod +x /usr/local/bin/micromamba
export MAMBA_ROOT_PREFIX=/opt/mamba
mkdir -p $MAMBA_ROOT_PREFIX
micromamba create -n bakta -y -c conda-forge -c bioconda bakta 2>&1 | tail -3
eval "$(micromamba shell hook -s bash)"
micromamba activate bakta
echo "bakta $(bakta --version 2>&1)"
echo "Installed: $(date -u)"

# DB setup via symlinks
DB_DIR="/opt/bakta_db"
mkdir -p "$DB_DIR"
for f in bakta.db psc.dmnd expert-protein-sequences.dmnd sorf.dmnd version.json \
         pfam.h3f pfam.h3i pfam.h3m pfam.h3p \
         antifam.h3f antifam.h3i antifam.h3m antifam.h3p \
         ncRNA-genes.i1f ncRNA-genes.i1i ncRNA-genes.i1m ncRNA-genes.i1p \
         ncRNA-regions.i1f ncRNA-regions.i1i ncRNA-regions.i1m ncRNA-regions.i1p \
         rRNA.i1f rRNA.i1i rRNA.i1m rRNA.i1p \
         oric.fna orit.fna rfam-go.tsv; do
    [ -f "/in/$f" ] && ln -s "/in/$f" "$DB_DIR/$f"
done

# AMRFinderPlus DB — must run amrfinder_update (symlinked AMR files don't work)
mkdir -p "$DB_DIR/amrfinderplus-db"
amrfinder_update --force_update --database "$DB_DIR/amrfinderplus-db/" 2>&1 | tail -1
echo "DB ready: $(date -u)"

# Find the chunk file
CHUNK=$(ls /in/chunk_*.fasta | head -1)
CHUNK_NAME=$(basename "$CHUNK" .fasta)
N_SEQS=$(grep -c "^>" "$CHUNK")
echo "Running: $CHUNK_NAME ($N_SEQS sequences) threads=$(nproc)"
echo "Annotation start: $(date -u)"

bakta_proteins \
    --db "$DB_DIR" \
    --output "$OUTPUT_DIR" \
    --prefix "$CHUNK_NAME" \
    --threads $(nproc) \
    --force \
    --verbose \
    "$CHUNK" 2>&1

echo "Annotation done: $(date -u)"
ls -lh "$OUTPUT_DIR/$CHUNK_NAME".*
