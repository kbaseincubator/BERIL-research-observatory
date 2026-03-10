#!/bin/bash
# Phase 4: Download MGnify Sourmash Sketch DBs
# Expected: ~1.1 GB total, minutes
set -euo pipefail

BASE_URL="ftp://ftp.ebi.ac.uk/pub/databases/metagenomics/mgnify_genomes"
DEST="/home/psdehal/pangenome_science/BERIL-research-observatory/data/mgnify_ingest/sourmash_dbs"

# Biomes with known sourmash DBs and their directory names
# Directory naming pattern: sourmash_db_{biome-with-dashes-to-hyphens}-{version-with-dots-to-hyphens}
declare -A BIOME_SOURMASH=(
    [human-gut]="v2.0.2:sourmash_db_human-gut-v2-0-2"
    [marine]="v2.0:sourmash_db_marine-v2-0"
    [mouse-gut]="v1.0:sourmash_db_mouse-gut-v1-0"
    [cow-rumen]="v1.0.1:sourmash_db_uhgp-v1-0-1"
    [chicken-gut]="v1.0.1:sourmash_db_uhgp-v1-0-1"
)

echo "=== Phase 4: MGnify Sourmash Sketch DB Download ==="
echo "Started: $(date)"

mkdir -p "$DEST"

for biome in "${!BIOME_SOURMASH[@]}"; do
    IFS=':' read -r version sourmash_dir <<< "${BIOME_SOURMASH[$biome]}"
    biome_url="$BASE_URL/$biome/$version"
    biome_dest="$DEST/$biome"
    mkdir -p "$biome_dest"

    echo ""
    echo "--- $biome ($version) ---"

    # List available sourmash files
    sourmash_files=$(curl -s --list-only "$biome_url/$sourmash_dir/" 2>/dev/null || echo "")
    if [ -z "$sourmash_files" ]; then
        # Try to discover the sourmash directory name
        echo "  Discovering sourmash directory..."
        all_dirs=$(curl -s --list-only "$biome_url/" 2>/dev/null | grep sourmash || echo "")
        if [ -n "$all_dirs" ]; then
            sourmash_dir=$(echo "$all_dirs" | head -1)
            sourmash_files=$(curl -s --list-only "$biome_url/$sourmash_dir/" 2>/dev/null || echo "")
        fi
    fi

    if [ -n "$sourmash_files" ]; then
        echo "  Found sourmash dir: $sourmash_dir"
        echo "$sourmash_files" | while read -r f; do
            [ -z "$f" ] && continue
            echo "  Downloading $f..."
            curl -C - -# -o "$biome_dest/$f" "$biome_url/$sourmash_dir/$f"
        done
    else
        echo "  No sourmash DB found"
    fi
done

# Also check biomes not in the hardcoded list
echo ""
echo "--- Checking remaining biomes for sourmash DBs ---"
for biome in soil sheep-rumen pig-gut marine_sediment honeybee-gut human-oral human-skin human-vaginal barley-rhizosphere maize-rhizosphere tomato-rhizosphere non-model-fish-gut zebrafish-fecal; do
    # Get latest version
    latest=$(curl -s --list-only "$BASE_URL/$biome/" 2>/dev/null | sort -V | tail -1)
    [ -z "$latest" ] && continue
    sourmash_dir=$(curl -s --list-only "$BASE_URL/$biome/$latest/" 2>/dev/null | grep sourmash | head -1 || echo "")
    if [ -n "$sourmash_dir" ]; then
        echo "  Found sourmash for $biome/$latest: $sourmash_dir"
        biome_dest="$DEST/$biome"
        mkdir -p "$biome_dest"
        curl -s --list-only "$BASE_URL/$biome/$latest/$sourmash_dir/" 2>/dev/null | while read -r f; do
            [ -z "$f" ] && continue
            echo "    Downloading $f..."
            curl -C - -# -o "$biome_dest/$f" "$BASE_URL/$biome/$latest/$sourmash_dir/$f"
        done
    fi
done

echo ""
echo "=== Phase 4 Complete ==="
echo "Finished: $(date)"
du -sh "$DEST"
