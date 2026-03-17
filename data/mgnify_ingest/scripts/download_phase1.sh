#!/bin/bash
# Phase 1: Download MGnify metadata & small files
# Expected total: ~200 MB, takes minutes
set -euo pipefail

BASE_URL="ftp://ftp.ebi.ac.uk/pub/databases/metagenomics"
DEST="/home/psdehal/pangenome_science/BERIL-research-observatory/data/mgnify_ingest"

echo "=== Phase 1: MGnify Metadata Download ==="
echo "Started: $(date)"

# --- Protein DB metadata ---
echo "--- Downloading protein database metadata ---"
mkdir -p "$DEST/metadata/protein_db"
for f in README.txt md5sum.txt mgy_biome_counts.tsv.gz; do
    echo "  Downloading $f..."
    curl -C - -# -o "$DEST/metadata/protein_db/$f" "$BASE_URL/peptide_database/current_release/$f"
done

# --- Genome catalogue metadata (latest version per biome) ---
# Map each biome to its latest version
declare -A BIOME_VERSIONS=(
    [human-gut]=v2.0.2
    [soil]=v1.0
    [marine]=v2.0
    [chicken-gut]=v1.0.1
    [cow-rumen]=v1.0.1
    [mouse-gut]=v1.0
    [pig-gut]=v1.0
    [sheep-rumen]=v1.0
    [marine_sediment]=v1.0
    [honeybee-gut]=v1.0.1
    [human-oral]=v1.0.1
    [human-skin]=v1.0
    [human-vaginal]=v1.0
    [barley-rhizosphere]=v2.0
    [maize-rhizosphere]=v1.0
    [tomato-rhizosphere]=v1.0
    [non-model-fish-gut]=v2.0
    [zebrafish-fecal]=v1.0
)

echo "--- Downloading genome catalogue metadata ---"
for biome in "${!BIOME_VERSIONS[@]}"; do
    version="${BIOME_VERSIONS[$biome]}"
    biome_dir="$DEST/metadata/genome_catalogues/$biome"
    mkdir -p "$biome_dir"

    biome_url="$BASE_URL/mgnify_genomes/$biome/$version"

    # Download metadata TSV
    echo "  $biome ($version): genomes-all_metadata.tsv"
    curl -C - -s -o "$biome_dir/genomes-all_metadata.tsv" "$biome_url/genomes-all_metadata.tsv" 2>/dev/null || echo "    WARN: metadata TSV not found for $biome"

    # Download README
    # README naming varies: README.txt, README_v2.0.2.txt, etc.
    for readme_pattern in "README.txt" "README_${version}.txt"; do
        curl -C - -s -o "$biome_dir/$readme_pattern" "$biome_url/$readme_pattern" 2>/dev/null && echo "    Got $readme_pattern" && break
    done
done

echo ""
echo "=== Phase 1 Complete ==="
echo "Finished: $(date)"
echo ""
echo "Files downloaded:"
find "$DEST/metadata" -type f | sort
echo ""
echo "Total size:"
du -sh "$DEST/metadata"
