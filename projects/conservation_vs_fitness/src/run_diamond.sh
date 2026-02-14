#!/bin/bash
# Run DIAMOND blastp searches for each FB organism against its mapped pangenome clades.
#
# Usage:
#   ./run_diamond.sh <organism_mapping.tsv> <fb_fastas_dir> <species_fastas_dir> <output_dir> [threads]
#
# Each FB organism is searched against the concatenated cluster rep FASTAs
# of all its mapped pangenome clades. Multi-clade resolution happens later
# in NB03 based on hit counts.
#
# Parameters:
#   --id 90         Minimum 90% protein identity (same-species comparison)
#   --max-target-seqs 1   Best hit only per query
#   blastp default mode   Fast — appropriate for high-identity same-species searches

set -euo pipefail

if [ $# -lt 4 ]; then
    echo "Usage: $0 <organism_mapping.tsv> <fb_fastas_dir> <species_fastas_dir> <output_dir> [threads]"
    echo ""
    echo "Arguments:"
    echo "  organism_mapping.tsv  TSV from NB01 (orgId, gtdb_species_clade_id, ...)"
    echo "  fb_fastas_dir         Directory with per-organism FB protein FASTAs"
    echo "  species_fastas_dir    Directory with per-species cluster rep FASTAs"
    echo "  output_dir            Directory for DIAMOND output TSVs"
    echo "  threads               Number of threads per DIAMOND search (default: 4)"
    exit 1
fi

MAPPING="$1"
FB_DIR="$2"
SPECIES_DIR="$3"
OUT_DIR="$4"
THREADS="${5:-4}"

mkdir -p "$OUT_DIR"

# Temp directory for concatenated targets and DBs
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

echo "=== DIAMOND search pipeline ==="
echo "Mapping:     $MAPPING"
echo "FB FASTAs:   $FB_DIR"
echo "Species FASTAs: $SPECIES_DIR"
echo "Output:      $OUT_DIR"
echo "Threads:     $THREADS"
echo ""

# Get unique organisms from mapping (skip header)
ORGANISMS=$(cut -f1 "$MAPPING" | tail -n+2 | sort -u)
N_ORGS=$(echo "$ORGANISMS" | wc -l)
echo "Organisms to process: $N_ORGS"
echo ""

COUNTER=0
SKIPPED=0
FAILED=0

for ORG in $ORGANISMS; do
    COUNTER=$((COUNTER + 1))

    # Check if FB FASTA exists
    if [ ! -f "${FB_DIR}/${ORG}.fasta" ]; then
        echo "  [$COUNTER/$N_ORGS] $ORG: SKIP (no FB FASTA)"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    # Skip if output already exists and is non-empty
    if [ -f "${OUT_DIR}/${ORG}.tsv" ] && [ -s "${OUT_DIR}/${ORG}.tsv" ]; then
        N_HITS=$(wc -l < "${OUT_DIR}/${ORG}.tsv")
        echo "  [$COUNTER/$N_ORGS] $ORG: cached ($N_HITS hits)"
        continue
    fi

    # Get mapped clades for this organism
    CLADES=$(awk -F'\t' -v org="$ORG" '$1==org {print $6}' "$MAPPING" | sort -u)

    if [ -z "$CLADES" ]; then
        echo "  [$COUNTER/$N_ORGS] $ORG: SKIP (no mapped clades)"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    # Concatenate species FASTAs for all mapped clades
    TARGET="${TMPDIR}/${ORG}_target.fasta"
    > "$TARGET"
    MISSING_CLADE=0
    for CLADE in $CLADES; do
        if [ -f "${SPECIES_DIR}/${CLADE}.fasta" ]; then
            cat "${SPECIES_DIR}/${CLADE}.fasta" >> "$TARGET"
        else
            echo "  WARNING: missing species FASTA for clade $CLADE"
            MISSING_CLADE=1
        fi
    done

    if [ ! -s "$TARGET" ]; then
        echo "  [$COUNTER/$N_ORGS] $ORG: SKIP (empty target)"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    # Build DIAMOND DB
    DB="${TMPDIR}/${ORG}_db"
    diamond makedb --in "$TARGET" --db "$DB" 2>/dev/null

    # Run DIAMOND blastp
    diamond blastp \
        --query "${FB_DIR}/${ORG}.fasta" \
        --db "$DB" \
        --out "${OUT_DIR}/${ORG}.tsv" \
        --outfmt 6 qseqid sseqid pident length qlen slen evalue bitscore \
        --id 90 \
        --max-target-seqs 1 \
        --threads "$THREADS" \
        2>/dev/null

    if [ $? -ne 0 ]; then
        echo "  [$COUNTER/$N_ORGS] $ORG: FAILED"
        FAILED=$((FAILED + 1))
        continue
    fi

    N_HITS=0
    if [ -f "${OUT_DIR}/${ORG}.tsv" ]; then
        N_HITS=$(wc -l < "${OUT_DIR}/${ORG}.tsv")
    fi

    N_QUERY=$(grep -c '^>' "${FB_DIR}/${ORG}.fasta")
    PCT=$(echo "scale=1; $N_HITS * 100 / $N_QUERY" | bc 2>/dev/null || echo "?")

    echo "  [$COUNTER/$N_ORGS] $ORG: $N_HITS/$N_QUERY hits ($PCT%)"

    # Clean up temp files for this organism
    rm -f "$TARGET" "${DB}".*
done

echo ""
echo "=== Done ==="
echo "Processed: $COUNTER organisms"
echo "Skipped:   $SKIPPED"
echo "Failed:    $FAILED"
echo "Results:   $OUT_DIR/"
