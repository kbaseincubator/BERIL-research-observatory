#!/bin/bash
set -eo pipefail

# Download Bakta full DB tarball and save to CTS output (MinIO)
# Don't extract — let the annotation job do that locally
OUTPUT_DIR="$1"

echo "=== Staging Bakta Full DB (compressed) ==="
echo "Output: $OUTPUT_DIR"
echo "Started: $(date)"

apt-get update -qq && apt-get install -y -qq wget > /dev/null 2>&1

# Download full DB from Zenodo (29.7 GB)
echo "=== Downloading Bakta DB v6.0 full ==="
wget --progress=dot:giga https://zenodo.org/records/14916843/files/db.tar.xz -O "$OUTPUT_DIR/db.tar.xz" 2>&1

echo "=== Download complete ==="
ls -lh "$OUTPUT_DIR/db.tar.xz"

echo "=== Finished: $(date) ==="
