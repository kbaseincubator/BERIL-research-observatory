#!/usr/bin/env bash
#
# Prepare InterPro files for BERDL ingestion.
#
# 1. Adds header line to protein2ipr.dat.gz (streaming, no full decompress)
# 2. Parses entry.list → interpro_entries.tsv
# 3. Parses interpro2go → interpro_go_mappings.tsv
#
# Usage:
#   bash data/interpro_lookup/scripts/03_prepare_for_ingest.sh

set -euo pipefail

BULK_DIR="data/interpro_lookup/bulk"
OUT_DIR="data/interpro_lookup/prepared"
LOG_FILE="data/interpro_lookup/prepare.log"

mkdir -p "$OUT_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# ── 1. protein2ipr: add header ──────────────────────────────────────
#
# protein2ipr.dat.gz is headerless TSV with columns:
#   uniprot_acc  ipr_id  ipr_desc  source_db  source_acc  start  stop
#
# We stream: decompress → prepend header → recompress
# This produces a new ~16GB file without needing 100GB temp space.

PROTEIN2IPR_IN="${BULK_DIR}/protein2ipr.dat.gz"
PROTEIN2IPR_OUT="${OUT_DIR}/protein2ipr.tsv.gz"

if [ -f "$PROTEIN2IPR_OUT" ]; then
    log "SKIP protein2ipr.tsv.gz (already exists)"
else
    if [ ! -f "$PROTEIN2IPR_IN" ]; then
        log "ERROR: ${PROTEIN2IPR_IN} not found. Run 02_download_interpro_bulk.sh first."
        exit 1
    fi

    log "Adding header to protein2ipr.dat.gz → protein2ipr.tsv.gz"
    log "  This streams through 16GB compressed data — expect ~10-20 minutes."

    # Verify format with first few lines
    log "  Verifying format (first 3 lines):"
    zcat "$PROTEIN2IPR_IN" | head -3 | tee -a "$LOG_FILE"

    NCOLS=$(zcat "$PROTEIN2IPR_IN" | head -1 | awk -F'\t' '{print NF}')
    log "  Detected $NCOLS columns"

    if [ "$NCOLS" -lt 6 ] || [ "$NCOLS" -gt 7 ]; then
        log "WARNING: Expected 6-7 columns, got $NCOLS. Check format."
    fi

    # Stream: header + decompressed data → recompressed
    (
        printf "uniprot_acc\tipr_id\tipr_desc\tsource_db\tsource_acc\tstart\tstop\n"
        zcat "$PROTEIN2IPR_IN"
    ) | gzip > "${PROTEIN2IPR_OUT}.tmp"

    mv "${PROTEIN2IPR_OUT}.tmp" "$PROTEIN2IPR_OUT"
    log "  Done: $(du -h "$PROTEIN2IPR_OUT" | cut -f1)"
fi

# ── 2. entry.list → interpro_entries.tsv ─────────────────────────────
#
# entry.list format (tab-separated, no header):
#   IPR000001  Domain  Kringle
#
ENTRY_IN="${BULK_DIR}/entry.list"
ENTRY_OUT="${OUT_DIR}/interpro_entries.tsv"

if [ -f "$ENTRY_OUT" ]; then
    log "SKIP interpro_entries.tsv (already exists)"
else
    if [ ! -f "$ENTRY_IN" ]; then
        log "SKIP entry.list (not downloaded)"
    else
        log "Parsing entry.list → interpro_entries.tsv"
        (
            printf "ipr_id\tentry_type\tentry_name\n"
            cat "$ENTRY_IN"
        ) > "$ENTRY_OUT"
        NLINES=$(wc -l < "$ENTRY_OUT")
        log "  Done: $((NLINES - 1)) entries"
    fi
fi

# ── 3. interpro2go → interpro_go_mappings.tsv ────────────────────────
#
# interpro2go format:
#   InterPro:IPR000001 Kringle > GO:blood coagulation ; GO:0007596
#
# We parse into:
#   ipr_id  go_id  go_name  go_category
#
GO_IN="${BULK_DIR}/interpro2go"
GO_OUT="${OUT_DIR}/interpro_go_mappings.tsv"

if [ -f "$GO_OUT" ]; then
    log "SKIP interpro_go_mappings.tsv (already exists)"
else
    if [ ! -f "$GO_IN" ]; then
        log "SKIP interpro2go (not downloaded)"
    else
        log "Parsing interpro2go → interpro_go_mappings.tsv"
        python3 -c "
import re, sys

with open('$GO_IN') as fin, open('$GO_OUT', 'w') as fout:
    fout.write('ipr_id\tgo_id\tgo_name\n')
    count = 0
    for line in fin:
        line = line.strip()
        if not line or line.startswith('!'):
            continue
        # Format: InterPro:IPR000001 Kringle > GO:blood coagulation ; GO:0007596
        m = re.match(r'InterPro:(IPR\d+)\s+.+>\s+GO:(.+)\s+;\s+(GO:\d+)', line)
        if m:
            ipr_id = m.group(1)
            go_name = m.group(2).strip()
            go_id = m.group(3)
            fout.write(f'{ipr_id}\t{go_id}\t{go_name}\n')
            count += 1
    print(f'  Parsed {count} GO mappings')
"
        NLINES=$(wc -l < "$GO_OUT")
        log "  Done: $((NLINES - 1)) mappings"
    fi
fi

log ""
log "=== Prepared files ==="
ls -lh "$OUT_DIR"/ 2>/dev/null | tee -a "$LOG_FILE"
