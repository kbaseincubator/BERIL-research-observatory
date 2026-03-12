#!/bin/bash
# Debug version — verbose logging at every step, single chunk

echo "=== BAKTA DEBUG JOB ==="
echo "Date: $(date -u)"
echo "Hostname: $(hostname)"
echo "CPUs: $(nproc)"
echo "Memory: $(free -h | awk '/Mem:/{print $2}')"
echo "Disk: $(df -h / | tail -1)"
echo "Kernel: $(uname -r)"
echo ""

OUTPUT_DIR="$1"
echo "Output dir: $OUTPUT_DIR"
echo "Input dir contents:"
ls -lh /in/ | head -20
echo "..."
echo "Total input files: $(ls /in/ | wc -l)"
echo ""

echo "=== Chunk files ==="
ls -lh /in/chunk_*.fasta 2>/dev/null || echo "NO CHUNK FILES FOUND"
echo ""

echo "=== DB files ==="
ls -lh /in/bakta.db /in/psc.dmnd /in/version.json 2>/dev/null || echo "SOME DB FILES MISSING"
echo ""

# Step 1: apt-get
echo "=== Step 1: apt-get ==="
echo "Starting apt-get at $(date -u)"
apt-get update -qq 2>&1 | tail -2
apt-get install -y -qq wget bzip2 2>&1 | tail -3
echo "apt-get done at $(date -u)"
echo ""

# Step 2: micromamba
echo "=== Step 2: micromamba ==="
echo "Starting micromamba install at $(date -u)"
wget -qO /usr/local/bin/micromamba \
  https://github.com/mamba-org/micromamba-releases/releases/latest/download/micromamba-linux-64
chmod +x /usr/local/bin/micromamba
export MAMBA_ROOT_PREFIX=/opt/mamba
mkdir -p $MAMBA_ROOT_PREFIX
echo "micromamba $(micromamba --version)"
echo "Creating bakta env..."
micromamba create -n bakta -y -c conda-forge -c bioconda bakta 2>&1 | tail -5
eval "$(micromamba shell hook -s bash)"
micromamba activate bakta
echo "bakta $(bakta --version 2>&1)"
echo "diamond $(diamond version 2>&1)"
echo "amrfinder: $(which amrfinder)"
echo "micromamba done at $(date -u)"
echo ""

# Step 3: Set up DB
echo "=== Step 3: DB setup ==="
echo "Starting DB setup at $(date -u)"
DB_DIR="/opt/bakta_db"
mkdir -p "$DB_DIR/amrfinderplus-db"

for f in bakta.db psc.dmnd expert-protein-sequences.dmnd sorf.dmnd version.json \
         pfam.h3f pfam.h3i pfam.h3m pfam.h3p \
         antifam.h3f antifam.h3i antifam.h3m antifam.h3p \
         ncRNA-genes.i1f ncRNA-genes.i1i ncRNA-genes.i1m ncRNA-genes.i1p \
         ncRNA-regions.i1f ncRNA-regions.i1i ncRNA-regions.i1m ncRNA-regions.i1p \
         rRNA.i1f rRNA.i1i rRNA.i1m rRNA.i1p \
         oric.fna orit.fna rfam-go.tsv; do
    if [ -f "/in/$f" ]; then
        ln -s "/in/$f" "$DB_DIR/$f"
        echo "  linked: $f"
    else
        echo "  MISSING: $f"
    fi
done

AMRDB_DIR="$DB_DIR/amrfinderplus-db/2024-12-18.1"
mkdir -p "$AMRDB_DIR"
for f in /in/AMR* /in/database_format_version.txt /in/fam.tsv /in/taxgroup.tsv /in/version.txt; do
    [ -f "$f" ] && ln -s "$f" "$AMRDB_DIR/" && echo "  linked AMR: $(basename $f)"
done
ln -sf "$AMRDB_DIR" "$DB_DIR/amrfinderplus-db/latest"

echo "DB version:"
cat "$DB_DIR/version.json"
echo ""
echo "DB setup done at $(date -u)"
echo ""

# Step 4: Run bakta_proteins on the chunk
echo "=== Step 4: bakta_proteins ==="
CHUNK=$(ls /in/chunk_*.fasta | head -1)
N_SEQS=$(grep -c "^>" "$CHUNK")
echo "Chunk: $CHUNK"
echo "Sequences: $N_SEQS"
echo "Threads: $(nproc)"
echo "Starting bakta_proteins at $(date -u)"

bakta_proteins \
    --db "$DB_DIR" \
    --output "$OUTPUT_DIR" \
    --prefix debug_chunk \
    --threads $(nproc) \
    --force \
    --verbose \
    "$CHUNK" 2>&1

echo ""
echo "bakta_proteins exit code: $?"
echo "Finished bakta_proteins at $(date -u)"
echo ""

# Step 5: Results
echo "=== Step 5: Results ==="
ls -lh "$OUTPUT_DIR"/debug_chunk.* 2>/dev/null || echo "NO OUTPUT FILES"
if [ -f "$OUTPUT_DIR/debug_chunk.tsv" ]; then
    TOTAL=$(awk 'END{print NR-1}' "$OUTPUT_DIR/debug_chunk.tsv")
    echo "Total annotated: $TOTAL"
    echo "First 5 lines:"
    head -8 "$OUTPUT_DIR/debug_chunk.tsv"
fi

echo ""
echo "=== DONE at $(date -u) ==="
