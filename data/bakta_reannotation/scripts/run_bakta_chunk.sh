#!/bin/bash
set -eo pipefail

# Bakta annotation worker for a single FASTA chunk
# Called by CTS with: run_bakta_chunk.sh /out/ /in/chunk_NNN.fasta
# DB tarball expected at /in/db.tar.xz

OUTPUT_DIR="$1"
shift
INPUT_FASTA="$1"
CHUNK_NAME=$(basename "$INPUT_FASTA" .fasta)

echo "=== Bakta Chunk Worker ==="
echo "Chunk: $CHUNK_NAME"
echo "Input: $INPUT_FASTA"
echo "Output: $OUTPUT_DIR"
echo "Started: $(date -u)"
echo "CPUs: $(nproc)"

# Install micromamba + bakta
apt-get update -qq && apt-get install -y -qq wget bzip2 xz-utils > /dev/null 2>&1
wget -qO /usr/local/bin/micromamba \
  https://github.com/mamba-org/micromamba-releases/releases/latest/download/micromamba-linux-64
chmod +x /usr/local/bin/micromamba
export MAMBA_ROOT_PREFIX=/opt/mamba
mkdir -p $MAMBA_ROOT_PREFIX
micromamba create -n bakta -y -c conda-forge -c bioconda bakta 2>&1 | tail -3
eval "$(micromamba shell hook -s bash)"
micromamba activate bakta
echo "bakta $(bakta --version 2>&1)"

# Extract DB
echo "=== Extracting Bakta DB ==="
tar xJf /in/db.tar.xz -C /opt/
DB_DIR=$(find /opt -name "version.json" -exec dirname {} \; | head -1)
echo "DB: $DB_DIR"

# AMRFinderPlus DB
mkdir -p "$DB_DIR/amrfinderplus-db"
amrfinder_update --force_update --database "$DB_DIR/amrfinderplus-db/" 2>&1 | tail -1

# Count sequences
N_SEQS=$(grep -c "^>" "$INPUT_FASTA")
echo "=== Annotating $N_SEQS sequences ==="

# Run bakta_proteins with all available CPUs
bakta_proteins \
    --db "$DB_DIR" \
    --output "$OUTPUT_DIR" \
    --prefix "$CHUNK_NAME" \
    --threads $(nproc) \
    --force \
    "$INPUT_FASTA" 2>&1

# Summary
echo "=== Results ==="
ls -lh "$OUTPUT_DIR/$CHUNK_NAME".*
TOTAL=$(awk 'END{print NR-1}' "$OUTPUT_DIR/$CHUNK_NAME.tsv")
HYPO=$(awk 'END{print NR-1}' "$OUTPUT_DIR/$CHUNK_NAME.hypotheticals.tsv")
echo "Annotated: $((TOTAL - HYPO)) / $TOTAL ($CHUNK_NAME)"
echo "=== Finished: $(date -u) ==="
