#!/bin/bash
set -eo pipefail

# Download all Bakta results from MinIO and combine into a single TSV
#
# Usage: bash collect_results.sh
#
# Outputs:
#   - data/bakta_reannotation/results/chunk_NNN.tsv (per-chunk)
#   - data/bakta_reannotation/results/all_bakta_annotations.tsv (combined)
#   - data/bakta_reannotation/results/summary.json

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/../results"
JOB_MANIFEST="$SCRIPT_DIR/../job_manifest.json"

mkdir -p "$RESULTS_DIR"

if [ ! -f "$JOB_MANIFEST" ]; then
    echo "ERROR: job_manifest.json not found"
    exit 1
fi

N_JOBS=$(python3 -c "import json; print(len(json.load(open('$JOB_MANIFEST'))['jobs']))")
echo "=== Collecting results from $N_JOBS jobs ==="

# Download TSV results for each chunk
DOWNLOADED=0
FAILED=0
for CHUNK_NAME in $(python3 -c "
import json
jobs = json.load(open('$JOB_MANIFEST'))['jobs']
for j in jobs:
    print(j['chunk'])
"); do
    TSV_PATH="cts/io/psdehal/bakta_reannotation/output/$CHUNK_NAME/$CHUNK_NAME.tsv"
    LOCAL_PATH="$RESULTS_DIR/$CHUNK_NAME.tsv"

    if [ -f "$LOCAL_PATH" ]; then
        echo "  $CHUNK_NAME.tsv (cached)"
        DOWNLOADED=$((DOWNLOADED + 1))
        continue
    fi

    if mc cp "berdl-minio/$TSV_PATH" "$LOCAL_PATH" 2>/dev/null; then
        echo "  $CHUNK_NAME.tsv ($(du -h "$LOCAL_PATH" | cut -f1))"
        DOWNLOADED=$((DOWNLOADED + 1))
    else
        echo "  $CHUNK_NAME.tsv MISSING"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "Downloaded: $DOWNLOADED / $N_JOBS"
if [ "$FAILED" -gt 0 ]; then
    echo "Failed: $FAILED (check job logs)"
fi

# Combine all TSVs into one
echo ""
echo "Combining into all_bakta_annotations.tsv..."
COMBINED="$RESULTS_DIR/all_bakta_annotations.tsv"
FIRST=true
for TSV in "$RESULTS_DIR"/chunk_*.tsv; do
    if [ "$FIRST" = true ]; then
        # Include header comments and column names
        cat "$TSV" > "$COMBINED"
        FIRST=false
    else
        # Skip comment lines and header row
        grep -v "^#" "$TSV" | tail -n +2 >> "$COMBINED"
    fi
done

TOTAL_LINES=$(wc -l < "$COMBINED")
echo "Combined: $COMBINED ($TOTAL_LINES lines, $(du -h "$COMBINED" | cut -f1))"

# Summary stats
echo ""
echo "=== Summary ==="
python3 << PYEOF
import os

combined = "$COMBINED"
total = 0
hypo = 0
has_gene = 0
has_ec = 0
has_go = 0
has_cog = 0
has_refseq = 0
has_uniparc = 0
has_uniref = 0

with open(combined) as f:
    headers = None
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
        if row.get("Gene", ""):
            has_gene += 1
        if row.get("EC", ""):
            has_ec += 1
        if row.get("GO", ""):
            has_go += 1
        if row.get("COG", ""):
            has_cog += 1
        if row.get("RefSeq", ""):
            has_refseq += 1
        if row.get("UniParc", ""):
            has_uniparc += 1
        if row.get("UniRef", ""):
            has_uniref += 1

ann = total - hypo
print(f"Total proteins:   {total:>12,}")
print(f"Annotated:        {ann:>12,}  ({ann/total*100:.1f}%)")
print(f"Hypothetical:     {hypo:>12,}  ({hypo/total*100:.1f}%)")
print(f"With Gene:        {has_gene:>12,}  ({has_gene/total*100:.1f}%)")
print(f"With EC:          {has_ec:>12,}  ({has_ec/total*100:.1f}%)")
print(f"With GO:          {has_go:>12,}  ({has_go/total*100:.1f}%)")
print(f"With COG:         {has_cog:>12,}  ({has_cog/total*100:.1f}%)")
print(f"With RefSeq:      {has_refseq:>12,}  ({has_refseq/total*100:.1f}%)")
print(f"With UniParc:     {has_uniparc:>12,}  ({has_uniparc/total*100:.1f}%)")
print(f"With UniRef:      {has_uniref:>12,}  ({has_uniref/total*100:.1f}%)")

import json
summary = {
    "total": total, "annotated": ann, "hypothetical": hypo,
    "gene": has_gene, "ec": has_ec, "go": has_go, "cog": has_cog,
    "refseq": has_refseq, "uniparc": has_uniparc, "uniref": has_uniref
}
with open("$RESULTS_DIR/summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(f"\nSummary written to results/summary.json")
PYEOF
