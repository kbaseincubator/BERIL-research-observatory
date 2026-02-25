#!/bin/bash
set -eo pipefail

# Bakta pilot: annotate 10K random cluster rep proteins
# Runs on CTS python test image
# Strategy: use micromamba (fast, single binary) for all deps

OUTPUT_DIR="$1"
shift
INPUT_FASTA="$1"

echo "=== Bakta Pilot ==="
echo "Input: $INPUT_FASTA"
echo "Output: $OUTPUT_DIR"
echo "Started: $(date)"
echo "CPUs: $(nproc)"

# Install micromamba (single static binary, much faster than conda)
echo "=== Installing micromamba ==="
apt-get update -qq 2>&1 | tail -1
apt-get install -y -qq wget bzip2 > /dev/null 2>&1

# Download micromamba
wget -qO /usr/local/bin/micromamba \
  https://github.com/mamba-org/micromamba-releases/releases/latest/download/micromamba-linux-64
chmod +x /usr/local/bin/micromamba
export MAMBA_ROOT_PREFIX=/opt/mamba
mkdir -p $MAMBA_ROOT_PREFIX

echo "micromamba version: $(micromamba --version)"

# Install bakta + all deps in one shot via micromamba
echo "=== Installing Bakta via micromamba (bioconda) ==="
micromamba create -n bakta -y -c conda-forge -c bioconda bakta 2>&1 | tail -10

# Activate
eval "$(micromamba shell hook -s bash)"
micromamba activate bakta

echo "bakta version: $(bakta --version 2>&1)"
echo "diamond version: $(diamond version 2>&1)"
echo "amrfinder: $(which amrfinder 2>&1)"

# Download Bakta DB (light version for pilot — 1.3 GB vs 29.7 GB full)
echo "=== Downloading Bakta DB (light) ==="
bakta_db download --output /opt/bakta_db --type light 2>&1 | tail -5
echo "=== DB download complete ==="
ls -lh /opt/bakta_db/db-light/ 2>/dev/null || ls -lh /opt/bakta_db/

# Count input sequences
N_SEQS=$(grep -c "^>" "$INPUT_FASTA")
echo "=== Running bakta_proteins on $N_SEQS sequences ==="

# Run bakta_proteins
bakta_proteins \
    --db /opt/bakta_db/db-light \
    --output "$OUTPUT_DIR" \
    --prefix bakta_pilot_10k \
    --threads 8 \
    --force \
    --verbose \
    "$INPUT_FASTA" 2>&1

echo "=== Results ==="
ls -lh "$OUTPUT_DIR"/bakta_pilot_10k.*

# Quick summary stats
echo ""
echo "=== Annotation Summary ==="
TOTAL=$(wc -l < "$OUTPUT_DIR/bakta_pilot_10k.tsv")
TOTAL=$((TOTAL - 1))
HYPO=$(wc -l < "$OUTPUT_DIR/bakta_pilot_10k.hypotheticals.tsv")
HYPO=$((HYPO - 1))
ANNOTATED=$((TOTAL - HYPO))
echo "Total proteins: $TOTAL"
echo "Annotated (non-hypothetical): $ANNOTATED"
echo "Hypothetical: $HYPO"
echo "Annotation rate: $(python3 -c "print(f'{$ANNOTATED/$TOTAL*100:.1f}%')")"

EC_COUNT=$(awk -F'\t' 'NR>1 && $5!="" {count++} END {print count+0}' "$OUTPUT_DIR/bakta_pilot_10k.tsv")
echo "With EC numbers: $EC_COUNT"
GO_COUNT=$(awk -F'\t' 'NR>1 && $6!="" {count++} END {print count+0}' "$OUTPUT_DIR/bakta_pilot_10k.tsv")
echo "With GO terms: $GO_COUNT"
COG_COUNT=$(awk -F'\t' 'NR>1 && $7!="" {count++} END {print count+0}' "$OUTPUT_DIR/bakta_pilot_10k.tsv")
echo "With COG: $COG_COUNT"
REFSEQ_COUNT=$(awk -F'\t' 'NR>1 && $8!="" {count++} END {print count+0}' "$OUTPUT_DIR/bakta_pilot_10k.tsv")
echo "With RefSeq WP_: $REFSEQ_COUNT"
UNIREF_COUNT=$(awk -F'\t' 'NR>1 && $10!="" {count++} END {print count+0}' "$OUTPUT_DIR/bakta_pilot_10k.tsv")
echo "With UniRef: $UNIREF_COUNT"

echo ""
echo "=== Sample output (first 5 rows) ==="
head -6 "$OUTPUT_DIR/bakta_pilot_10k.tsv"

echo ""
echo "=== Finished: $(date) ==="
