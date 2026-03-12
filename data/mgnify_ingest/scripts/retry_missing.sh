#!/bin/bash
# Retry downloading missing .faa files (and all other genome files) for species
# where the directory exists but .faa is missing.
# Uses fewer parallel connections to avoid FTP throttling.
set -euo pipefail

BASE_URL="ftp://ftp.ebi.ac.uk/pub/databases/metagenomics/mgnify_genomes"
METADATA_DIR="/home/psdehal/pangenome_science/BERIL-research-observatory/data/mgnify_ingest/metadata/genome_catalogues"
DEST="/home/psdehal/pangenome_science/BERIL-research-observatory/data/mgnify_ingest/genome_catalogues"
PARALLEL=8  # fewer connections for retry

declare -A BIOME_VERSIONS=(
    [human-gut]=v2.0.2
    [soil]=v1.0
    [marine]=v2.0
)

GENOME_SUFFIXES=(.faa .fna .gff _eggNOG.tsv _InterProScan.tsv _kegg_modules.tsv _kegg_classes.tsv _cog_summary.tsv _cazy_summary.tsv _annotation_coverage.tsv _rRNAs.fasta .fna.fai)
# Additional suffixes found in newer catalogues (soil, marine)
EXTRA_SUFFIXES=(_amrfinderplus.tsv _antismash.gff _crisprcasfinder.gff _crisprcasfinder.tsv _dbcan.gff _defense_finder.gff _gecco.gff _kegg_pathways.tsv _mobilome.gff _sanntis.gff)

for biome in "${@:-human-gut soil marine}"; do
    version="${BIOME_VERSIONS[$biome]}"
    biome_url="$BASE_URL/$biome/$version"
    biome_dest="$DEST/$biome"
    missing_file="/tmp/mgnify_${biome}_missing.txt"

    if [ ! -f "$missing_file" ]; then
        echo "Generating missing list for $biome..."
        expected="$biome_dest/species_rep_ids.txt"
        find "$biome_dest/species_catalogue" -name "*.faa" 2>/dev/null | xargs -I{} basename {} .faa | sort > "/tmp/mgnify_${biome}_downloaded.txt"
        sort "$expected" > "/tmp/mgnify_${biome}_expected.txt"
        comm -23 "/tmp/mgnify_${biome}_expected.txt" "/tmp/mgnify_${biome}_downloaded.txt" > "$missing_file"
    fi

    missing_count=$(wc -l < "$missing_file")
    echo ""
    echo "=== Retrying $biome: $missing_count missing species ==="
    echo "Started: $(date)"

    # Build URL list for missing species
    url_list="$biome_dest/.retry_urls.tsv"
    > "$url_list"

    while read -r sid; do
        bucket="${sid:0:${#sid}-2}"
        species_url="$biome_url/species_catalogue/$bucket/$sid"
        species_dest="$biome_dest/species_catalogue/$bucket/$sid"

        for suffix in "${GENOME_SUFFIXES[@]}" "${EXTRA_SUFFIXES[@]}"; do
            fname="${sid}${suffix}"
            dest_file="$species_dest/genome/$fname"
            if [ ! -f "$dest_file" ]; then
                printf '%s\t%s\n' "$dest_file" "$species_url/genome/$fname" >> "$url_list"
            fi
        done

        for fname in core_genes.txt gene_presence_absence.Rtab pan-genome.fna mashtree.nwk; do
            dest_file="$species_dest/pan-genome/$fname"
            if [ ! -f "$dest_file" ]; then
                printf '%s\t%s\n' "$dest_file" "$species_url/pan-genome/$fname" >> "$url_list"
            fi
        done
    done < "$missing_file"

    url_count=$(wc -l < "$url_list")
    echo "Files to download: $url_count"

    # Create directories
    awk -F'\t' '{print $1}' "$url_list" | xargs -I{} dirname {} | sort -u | xargs mkdir -p

    # Download with retry logic: curl with --retry
    local_start=$(date +%s)

    awk -F'\t' '{print $1 "\t" $2}' "$url_list" | \
        xargs -P "$PARALLEL" -d '\n' -I {} bash -c '
            dest=$(echo "{}" | cut -f1)
            url=$(echo "{}" | cut -f2)
            curl -s --retry 3 --retry-delay 5 --connect-timeout 15 --max-time 300 -o "$dest" "$url" 2>/dev/null
            if [ -f "$dest" ] && [ ! -s "$dest" ]; then
                rm -f "$dest"
            fi
        '

    # Clean up
    find "$biome_dest/species_catalogue" -type d -name "pan-genome" -empty -delete 2>/dev/null || true
    rm -f "$url_list"

    # Report
    new_faa=$(find "$biome_dest/species_catalogue" -name "*.faa" 2>/dev/null | wc -l)
    elapsed=$(( $(date +%s) - local_start ))
    echo "Completed $biome retry: $(date)"
    echo "  Elapsed: ${elapsed}s"
    echo "  Species with .faa now: $new_faa"
    echo "  Previously missing: $missing_count"
    echo "  Still missing: $(( missing_count - (new_faa - ($(wc -l < "$biome_dest/species_rep_ids.txt") - missing_count)) ))"
done
