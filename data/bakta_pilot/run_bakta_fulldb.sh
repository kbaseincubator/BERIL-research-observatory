#!/bin/bash
set -eo pipefail

# Bakta pilot with FULL DB
# Expects: $1 = output dir, $2 = input FASTA
# DB tarball is at /in/db.tar.xz (pre-staged on MinIO)

OUTPUT_DIR="$1"
shift
INPUT_FASTA="$1"

echo "=== Bakta Pilot (Full DB) ==="
echo "Input: $INPUT_FASTA"
echo "Output: $OUTPUT_DIR"
echo "Started: $(date)"
echo "CPUs: $(nproc)"

# Install micromamba + bakta
echo "=== Installing micromamba + bakta ==="
apt-get update -qq && apt-get install -y -qq wget bzip2 xz-utils > /dev/null 2>&1
wget -qO /usr/local/bin/micromamba \
  https://github.com/mamba-org/micromamba-releases/releases/latest/download/micromamba-linux-64
chmod +x /usr/local/bin/micromamba
export MAMBA_ROOT_PREFIX=/opt/mamba
mkdir -p $MAMBA_ROOT_PREFIX
micromamba create -n bakta -y -c conda-forge -c bioconda bakta 2>&1 | tail -5
eval "$(micromamba shell hook -s bash)"
micromamba activate bakta
echo "bakta version: $(bakta --version 2>&1)"

# Extract DB tarball from MinIO-staged input
echo "=== Extracting Bakta DB ==="
echo "Tarball: $(ls -lh /in/db.tar.xz)"
tar xJf /in/db.tar.xz -C /opt/
DB_DIR=$(find /opt -name "version.json" -exec dirname {} \; | head -1)
echo "DB directory: $DB_DIR"
ls -lh "$DB_DIR/" | head -10

# Setup AMRFinderPlus DB
echo "=== Setting up AMRFinderPlus DB ==="
mkdir -p "$DB_DIR/amrfinderplus-db"
amrfinder_update --force_update --database "$DB_DIR/amrfinderplus-db/" 2>&1 | tail -3

# Count input sequences
N_SEQS=$(grep -c "^>" "$INPUT_FASTA")
echo "=== Running bakta_proteins on $N_SEQS sequences (FULL DB) ==="

# Run bakta_proteins
bakta_proteins \
    --db "$DB_DIR" \
    --output "$OUTPUT_DIR" \
    --prefix bakta_pilot_10k_fulldb \
    --threads 8 \
    --force \
    --verbose \
    "$INPUT_FASTA" 2>&1

echo "=== Results ==="
ls -lh "$OUTPUT_DIR"/bakta_pilot_10k_fulldb.*

# Annotation summary
echo ""
echo "=== Annotation Summary ==="
TSV_PATH="$OUTPUT_DIR/bakta_pilot_10k_fulldb.tsv" python3 << 'PYEOF'
import csv, sys, os

tsv_path = os.environ["TSV_PATH"]
rows = []
headers = None
with open(tsv_path) as f:
    for line in f:
        if line.startswith("#"):
            continue
        parts = line.strip().split("\t")
        if headers is None:
            headers = parts
            continue
        row = dict(zip(headers, parts + [""] * (len(headers) - len(parts))))
        rows.append(row)

total = len(rows)
hypo = sum(1 for r in rows if r.get("Product", "") == "hypothetical protein")
annotated = total - hypo

print(f"Total proteins: {total:,}")
print(f"Annotated: {annotated:,} ({annotated/total*100:.1f}%)")
print(f"Hypothetical: {hypo:,} ({hypo/total*100:.1f}%)")
print()

for field in ["Gene", "Product", "EC", "GO", "COG", "RefSeq", "UniParc", "UniRef"]:
    count = sum(1 for r in rows if r.get(field, "") not in ("", "hypothetical protein"))
    print(f"  {field:12s}: {count:>6,} / {total:,}  ({count/total*100:.1f}%)")

uniref100 = sum(1 for r in rows if "UniRef100" in r.get("UniRef", ""))
uniref90 = sum(1 for r in rows if "UniRef90" in r.get("UniRef", ""))
uniref50 = sum(1 for r in rows if "UniRef50" in r.get("UniRef", ""))
print(f"\n  UniRef breakdown:")
print(f"    UniRef100 (exact hash match): {uniref100:,} ({uniref100/total*100:.1f}%)")
print(f"    UniRef90 (Diamond PSC):       {uniref90:,} ({uniref90/total*100:.1f}%)")
print(f"    UniRef50 (Diamond PSCC):      {uniref50:,} ({uniref50/total*100:.1f}%)")
PYEOF

echo ""
echo "=== Sample output (first 10 rows) ==="
head -13 "$OUTPUT_DIR/bakta_pilot_10k_fulldb.tsv"

echo ""
echo "=== Finished: $(date) ==="
