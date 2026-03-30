#!/bin/bash
# Phase 3: Download MGnify Genome Catalogue Species Representatives
# Uses parallel curl downloads (no wget dependency)
# Run: nohup bash download_phase3.sh human-gut soil marine > ../logs/phase3.log 2>&1 &
set -euo pipefail

BASE_URL="ftp://ftp.ebi.ac.uk/pub/databases/metagenomics/mgnify_genomes"
METADATA_DIR="/home/psdehal/pangenome_science/BERIL-research-observatory/data/mgnify_ingest/metadata/genome_catalogues"
DEST="/home/psdehal/pangenome_science/BERIL-research-observatory/data/mgnify_ingest/genome_catalogues"
PARALLEL=16

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

PRIORITY_BIOMES=(
    human-gut soil marine mouse-gut cow-rumen chicken-gut pig-gut sheep-rumen
    marine_sediment honeybee-gut human-oral human-skin human-vaginal
    barley-rhizosphere maize-rhizosphere tomato-rhizosphere
    non-model-fish-gut zebrafish-fecal
)

# Worker function: download a single file given tab-separated "dest\turl"
do_download() {
    local dest="$1"
    local url="$2"
    curl -s --connect-timeout 10 --max-time 300 -o "$dest" "$url" 2>/dev/null
    # Remove empty/error files
    if [ -f "$dest" ] && [ ! -s "$dest" ]; then
        rm -f "$dest"
    fi
}
export -f do_download

download_biome() {
    local biome="$1"
    local version="${BIOME_VERSIONS[$biome]}"
    local biome_dest="$DEST/$biome"
    local biome_url="$BASE_URL/$biome/$version"

    echo ""
    echo "=== Downloading species catalogue: $biome ($version) ==="
    echo "Started: $(date)"

    mkdir -p "$biome_dest"

    local meta_file="$METADATA_DIR/$biome/genomes-all_metadata.tsv"
    if [ ! -f "$meta_file" ]; then
        echo "ERROR: metadata file not found: $meta_file"
        return 1
    fi

    local species_list="$biome_dest/species_rep_ids.txt"
    awk -F'\t' 'NR>1 && $1==$14 {print $1}' "$meta_file" > "$species_list"
    local total=$(wc -l < "$species_list")
    echo "Species representatives to download: $total"

    # Build a tab-separated URL list: dest\turl
    local url_list="$biome_dest/.download_urls.tsv"
    > "$url_list"

    local genome_suffixes=(.faa .fna .gff _eggNOG.tsv _InterProScan.tsv _kegg_modules.tsv _kegg_classes.tsv _cog_summary.tsv _cazy_summary.tsv _annotation_coverage.tsv _rRNAs.fasta)

    echo "Building download URL list..."
    while read -r species_id; do
        local bucket="${species_id:0:${#species_id}-2}"
        local species_url="$biome_url/species_catalogue/$bucket/$species_id"
        local species_dest="$biome_dest/species_catalogue/$bucket/$species_id"

        for suffix in "${genome_suffixes[@]}"; do
            local fname="${species_id}${suffix}"
            local dest_file="$species_dest/genome/$fname"
            if [ ! -f "$dest_file" ]; then
                printf '%s\t%s\n' "$dest_file" "$species_url/genome/$fname" >> "$url_list"
            fi
        done

        for fname in core_genes.txt gene_presence_absence.Rtab pan-genome.fna mashtree.nwk; do
            local dest_file="$species_dest/pan-genome/$fname"
            if [ ! -f "$dest_file" ]; then
                printf '%s\t%s\n' "$dest_file" "$species_url/pan-genome/$fname" >> "$url_list"
            fi
        done
    done < "$species_list"

    local url_count=$(wc -l < "$url_list")
    echo "Files to download: $url_count (skipping already downloaded)"

    if [ "$url_count" -eq 0 ]; then
        echo "All files already downloaded for $biome"
        return 0
    fi

    # Create all directories first
    awk -F'\t' '{print $1}' "$url_list" | xargs -I{} dirname {} | sort -u | xargs mkdir -p

    # Download in parallel
    local start_time=$(date +%s)

    # Use a simple counter file for progress
    local progress_file="$biome_dest/.progress_count"
    echo "0" > "$progress_file"

    # Start a background progress reporter
    (
        while [ -f "$progress_file" ]; do
            sleep 60
            if [ -f "$progress_file" ]; then
                local faa_count=$(find "$biome_dest/species_catalogue" -name "*.faa" 2>/dev/null | wc -l)
                local elapsed=$(( $(date +%s) - start_time ))
                echo "  Progress: $faa_count / $total species downloaded (${elapsed}s elapsed) - $(date)"
            fi
        done
    ) &
    local reporter_pid=$!

    # Run parallel downloads
    awk -F'\t' '{print $1 "\t" $2}' "$url_list" | \
        xargs -P "$PARALLEL" -d '\n' -I {} bash -c '
            dest=$(echo "{}" | cut -f1)
            url=$(echo "{}" | cut -f2)
            curl -s --connect-timeout 10 --max-time 300 -o "$dest" "$url" 2>/dev/null
            if [ -f "$dest" ] && [ ! -s "$dest" ]; then
                rm -f "$dest"
            fi
        '

    # Stop progress reporter
    rm -f "$progress_file"
    kill $reporter_pid 2>/dev/null || true
    wait $reporter_pid 2>/dev/null || true

    # Clean up empty pan-genome directories
    find "$biome_dest/species_catalogue" -type d -name "pan-genome" -empty -delete 2>/dev/null || true

    local faa_count=$(find "$biome_dest/species_catalogue" -name "*.faa" 2>/dev/null | wc -l)
    local elapsed=$(( $(date +%s) - start_time ))
    echo "Completed $biome: $(date)"
    echo "  Elapsed: ${elapsed}s"
    echo "  Species with .faa: $faa_count / $total"
    echo "  Size: $(du -sh "$biome_dest" | cut -f1)"

    rm -f "$url_list"
}

if [ $# -ge 1 ]; then
    for biome in "$@"; do
        if [[ -v BIOME_VERSIONS[$biome] ]]; then
            download_biome "$biome"
        else
            echo "ERROR: Unknown biome '$biome'"
            echo "Available: ${!BIOME_VERSIONS[*]}"
            exit 1
        fi
    done
else
    echo "=== Phase 3: Downloading all genome catalogue species reps ==="
    echo "Started: $(date)"
    for biome in "${PRIORITY_BIOMES[@]}"; do
        download_biome "$biome"
    done
    echo ""
    echo "=== Phase 3 Complete ==="
    echo "Finished: $(date)"
    du -sh "$DEST"
fi
