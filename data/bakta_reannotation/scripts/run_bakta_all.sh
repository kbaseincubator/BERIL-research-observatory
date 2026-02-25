#!/bin/bash
set -eo pipefail

# Bakta annotation — single CTS job processing ALL chunks in parallel
#
# Input files (on MinIO):
#   /in/run_bakta_all.sh       — this script
#   /in/chunks.tar             — all FASTA chunks (not compressed)
#   /in/db.tar.xz              — Bakta full DB (xz compressed)
#
# Uses GNU parallel to run ~20 bakta_proteins instances × 8 threads each

OUTPUT_DIR="$1"

echo "=== Bakta Full Reannotation ==="
echo "Output: $OUTPUT_DIR"
echo "Started: $(date -u)"
echo "CPUs: $(nproc)"
echo "Memory: $(free -h | awk '/Mem:/{print $2}')"

NCPUS=$(nproc)
THREADS_PER_JOB=8
PARALLEL_JOBS=$((NCPUS / THREADS_PER_JOB))
echo "Plan: $PARALLEL_JOBS parallel jobs × $THREADS_PER_JOB threads each"

# --- Install dependencies ---
echo "=== Installing dependencies ==="
apt-get update -qq && apt-get install -y -qq wget bzip2 xz-utils parallel > /dev/null 2>&1
wget -qO /usr/local/bin/micromamba \
  https://github.com/mamba-org/micromamba-releases/releases/latest/download/micromamba-linux-64
chmod +x /usr/local/bin/micromamba
export MAMBA_ROOT_PREFIX=/opt/mamba
mkdir -p $MAMBA_ROOT_PREFIX
micromamba create -n bakta -y -c conda-forge -c bioconda bakta 2>&1 | tail -3
eval "$(micromamba shell hook -s bash)"
micromamba activate bakta
echo "bakta $(bakta --version 2>&1)"

# --- Extract DB ---
echo "=== Extracting Bakta DB ==="
tar xJf /in/db.tar.xz -C /opt/
DB_DIR=$(find /opt -name "version.json" -exec dirname {} \; | head -1)
echo "DB: $DB_DIR"
mkdir -p "$DB_DIR/amrfinderplus-db"
amrfinder_update --force_update --database "$DB_DIR/amrfinderplus-db/" 2>&1 | tail -1

# --- Extract FASTA chunks ---
echo "=== Extracting FASTA chunks ==="
mkdir -p /work/chunks
tar xf /in/chunks.tar -C /work/chunks/
N_CHUNKS=$(ls /work/chunks/*.fasta 2>/dev/null | wc -l)
echo "Found $N_CHUNKS chunks"
ls -lh /work/chunks/ | head -5
echo "..."

# --- Create per-chunk output dirs ---
mkdir -p /work/results

# --- Worker function for GNU parallel ---
cat > /work/run_one_chunk.sh << 'WORKER'
#!/bin/bash
CHUNK_FASTA="$1"
DB_DIR="$2"
THREADS="$3"
OUTPUT_BASE="$4"

CHUNK_NAME=$(basename "$CHUNK_FASTA" .fasta)
CHUNK_OUT="$OUTPUT_BASE/$CHUNK_NAME"
mkdir -p "$CHUNK_OUT"

eval "$(micromamba shell hook -s bash)"
micromamba activate bakta

N_SEQS=$(grep -c "^>" "$CHUNK_FASTA")
echo "[$(date -u '+%H:%M:%S')] START $CHUNK_NAME ($N_SEQS seqs)"

bakta_proteins \
    --db "$DB_DIR" \
    --output "$CHUNK_OUT" \
    --prefix "$CHUNK_NAME" \
    --threads "$THREADS" \
    --force \
    "$CHUNK_FASTA" > "$CHUNK_OUT/$CHUNK_NAME.stdout" 2>&1

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    TOTAL=$(awk 'END{print NR-1}' "$CHUNK_OUT/$CHUNK_NAME.tsv" 2>/dev/null || echo "?")
    echo "[$(date -u '+%H:%M:%S')] DONE  $CHUNK_NAME — $TOTAL proteins annotated"
else
    echo "[$(date -u '+%H:%M:%S')] FAIL  $CHUNK_NAME — exit code $EXIT_CODE"
fi
WORKER
chmod +x /work/run_one_chunk.sh

# --- Run all chunks in parallel ---
echo "=== Running $N_CHUNKS chunks ($PARALLEL_JOBS parallel × $THREADS_PER_JOB threads) ==="
echo "Started annotation: $(date -u)"

export MAMBA_ROOT_PREFIX=/opt/mamba

ls /work/chunks/*.fasta | parallel \
    --jobs "$PARALLEL_JOBS" \
    --halt soon,fail=10% \
    --progress \
    /work/run_one_chunk.sh {} "$DB_DIR" "$THREADS_PER_JOB" /work/results

echo "Finished annotation: $(date -u)"

# --- Collect results into output dir ---
echo "=== Collecting results ==="

# Copy all TSV, hypotheticals, and inference files to output
for CHUNK_DIR in /work/results/chunk_*; do
    CHUNK_NAME=$(basename "$CHUNK_DIR")
    for EXT in tsv hypotheticals.tsv inference.tsv json; do
        SRC="$CHUNK_DIR/$CHUNK_NAME.$EXT"
        if [ -f "$SRC" ]; then
            cp "$SRC" "$OUTPUT_DIR/"
        fi
    done
done

# Create combined TSV
echo "=== Creating combined annotation TSV ==="
COMBINED="$OUTPUT_DIR/all_bakta_annotations.tsv"
FIRST=true
for TSV in "$OUTPUT_DIR"/chunk_*.tsv; do
    [ -f "$TSV" ] || continue
    # Skip hypotheticals and inference files
    echo "$TSV" | grep -q "hypotheticals\|inference" && continue
    if [ "$FIRST" = true ]; then
        cat "$TSV" > "$COMBINED"
        FIRST=false
    else
        grep -v "^#" "$TSV" | tail -n +2 >> "$COMBINED"
    fi
done

# --- Summary ---
echo "=== Final Summary ==="
python3 << 'PYEOF'
import os, glob

combined = os.environ.get("OUTPUT_DIR", "/out") + "/all_bakta_annotations.tsv"
if not os.path.exists(combined):
    print("Combined TSV not found!")
    exit(1)

total = 0
hypo = 0
has_ec = 0
has_refseq = 0
has_uniparc = 0

headers = None
with open(combined) as f:
    for line in f:
        if line.startswith("#"):
            continue
        parts = line.strip().split("\t")
        if headers is None:
            headers = parts
            continue
        row = dict(zip(headers, parts + [""] * (len(headers) - len(parts))))
        total += 1
        if row.get("Product", "") == "hypothetical protein":
            hypo += 1
        if row.get("EC", ""):
            has_ec += 1
        if row.get("RefSeq", ""):
            has_refseq += 1
        if row.get("UniParc", ""):
            has_uniparc += 1

ann = total - hypo
print(f"Total proteins:  {total:>12,}")
print(f"Annotated:       {ann:>12,}  ({ann/total*100:.1f}%)")
print(f"Hypothetical:    {hypo:>12,}  ({hypo/total*100:.1f}%)")
print(f"With EC:         {has_ec:>12,}  ({has_ec/total*100:.1f}%)")
print(f"With RefSeq:     {has_refseq:>12,}  ({has_refseq/total*100:.1f}%)")
print(f"With UniParc:    {has_uniparc:>12,}  ({has_uniparc/total*100:.1f}%)")
PYEOF

echo ""
ls -lh "$OUTPUT_DIR/all_bakta_annotations.tsv"
echo "=== Finished: $(date -u) ==="
