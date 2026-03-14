#!/usr/bin/env bash
#
# Download InterPro bulk data files from EBI FTP.
#
# Downloads:
#   protein2ipr.dat.gz  — 16GB, UniProt accession → InterPro entry mappings
#   entry.list          — InterPro entry descriptions and types
#   interpro2go         — InterPro → GO term mappings
#
# Features:
#   - Resumable downloads (wget -c)
#   - MD5 checksum verification
#   - Progress logging
#
# Usage:
#   bash data/interpro_lookup/scripts/02_download_interpro_bulk.sh

set -euo pipefail

BASE_URL="https://ftp.ebi.ac.uk/pub/databases/interpro/current_release"
OUT_DIR="data/interpro_lookup/bulk"
LOG_FILE="data/interpro_lookup/download.log"

mkdir -p "$OUT_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

download_file() {
    local filename="$1"
    local url="${BASE_URL}/${filename}"
    local outpath="${OUT_DIR}/${filename}"

    if [ -f "$outpath" ] && [ ! -f "${outpath}.incomplete" ]; then
        log "SKIP $filename (already exists)"
        return 0
    fi

    log "DOWNLOADING $filename from $url"
    touch "${outpath}.incomplete"

    # wget with resume, retries, and timeout
    if wget -c \
        --tries=10 \
        --wait=5 \
        --waitretry=30 \
        --timeout=300 \
        --read-timeout=300 \
        --progress=dot:giga \
        -O "$outpath" \
        "$url" 2>&1 | tee -a "$LOG_FILE"; then
        rm -f "${outpath}.incomplete"
        log "DONE $filename ($(du -h "$outpath" | cut -f1))"
    else
        log "FAILED $filename — will resume on next run"
        return 1
    fi
}

verify_checksum() {
    local filename="$1"
    local outpath="${OUT_DIR}/${filename}"
    local md5_url="${BASE_URL}/${filename}.md5"
    local md5_file="${OUT_DIR}/${filename}.md5"

    if [ ! -f "$outpath" ]; then
        log "SKIP checksum for $filename (file not found)"
        return 1
    fi

    log "Downloading MD5 for $filename..."
    if wget -q -O "$md5_file" "$md5_url" 2>/dev/null; then
        local expected
        expected=$(awk '{print $1}' "$md5_file")
        local actual
        actual=$(md5sum "$outpath" | awk '{print $1}')

        if [ "$expected" = "$actual" ]; then
            log "CHECKSUM OK $filename"
            return 0
        else
            log "CHECKSUM FAIL $filename (expected=$expected actual=$actual)"
            return 1
        fi
    else
        log "WARN no MD5 available for $filename, skipping verification"
        return 0
    fi
}

# ── Main ─────────────────────────────────────────────────────────────
log "=== InterPro bulk download starting ==="
log "Output directory: $OUT_DIR"

# Small files first
download_file "entry.list"
download_file "interpro2go"

# Main mapping file (16GB)
log ""
log "=== Downloading protein2ipr.dat.gz (16GB — this will take a while) ==="
log "If interrupted, re-run this script to resume."
download_file "protein2ipr.dat.gz"

# Verify checksums
log ""
log "=== Verifying checksums ==="
verify_checksum "protein2ipr.dat.gz"

log ""
log "=== Download complete ==="
log "Files:"
ls -lh "$OUT_DIR"/ | tee -a "$LOG_FILE"
