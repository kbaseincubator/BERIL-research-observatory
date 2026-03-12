#!/bin/bash
# Phase 2: Download MGnify Protein Cluster Data
# Expected: ~129 GB compressed, takes hours
# Run in background: nohup bash download_phase2.sh > ../logs/phase2.log 2>&1 &
set -euo pipefail

BASE_URL="ftp://ftp.ebi.ac.uk/pub/databases/metagenomics/peptide_database/current_release"
DEST="/home/psdehal/pangenome_science/BERIL-research-observatory/data/mgnify_ingest/protein_db"

mkdir -p "$DEST"

echo "=== Phase 2: MGnify Protein Cluster Data Download ==="
echo "Started: $(date)"

# Files to download (in order of priority/size)
FILES=(
    "mgy_clusters.tsv.gz"          # 7.9 GB - cluster stats
    "mgy_biomes.tsv.gz"            # 7.7 GB - protein-biome mapping
    "mgy_counts.tsv.gz"            # 6.8 GB - per-protein counts
    "mgy_assemblies.tsv.gz"        # 10.9 GB - protein-assembly mapping
    "mgy_cluster_seqs.tsv.gz"      # 16.8 GB - cluster membership
    "mgy_clusters.fa.gz"           # 79 GB - cluster rep sequences (largest, last)
)

for f in "${FILES[@]}"; do
    echo ""
    echo "--- Downloading $f ---"
    echo "  Started: $(date)"
    curl -C - --progress-bar -o "$DEST/$f" "$BASE_URL/$f"
    echo "  Completed: $(date)"
    ls -lh "$DEST/$f"
done

# Download md5sums for verification
echo ""
echo "--- Downloading md5sum.txt ---"
curl -C - -s -o "$DEST/md5sum.txt" "$BASE_URL/md5sum.txt"

echo ""
echo "=== Verifying checksums ==="
cd "$DEST"
# Only check the files we downloaded (md5sum.txt may reference files we skipped)
for f in "${FILES[@]}"; do
    if [ -f "$f" ]; then
        expected=$(grep "$f" md5sum.txt | awk '{print $1}')
        if [ -n "$expected" ]; then
            actual=$(md5sum "$f" | awk '{print $1}')
            if [ "$expected" = "$actual" ]; then
                echo "  OK: $f"
            else
                echo "  FAIL: $f (expected $expected, got $actual)"
            fi
        else
            echo "  SKIP: $f (no checksum in md5sum.txt)"
        fi
    fi
done

echo ""
echo "=== Phase 2 Complete ==="
echo "Finished: $(date)"
du -sh "$DEST"
