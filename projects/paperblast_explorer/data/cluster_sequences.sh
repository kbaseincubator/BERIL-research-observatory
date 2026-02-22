#!/bin/bash
set -euo pipefail

# cluster_sequences.sh — Run MMseqs2 clustering at multiple identity levels
# Usage: cluster_sequences.sh /out/ /in/sequences.fasta
# Installs MMseqs2, clusters at 90%, 50%, 30% identity

OUTPUT_DIR="$1"
shift
INPUT_FASTA="$1"

echo "=== Starting MMseqs2 clustering pipeline ==="
echo "Input: $INPUT_FASTA"
echo "Output: $OUTPUT_DIR"
date

# Install MMseqs2
echo "--- Installing MMseqs2 ---"
apt-get update -qq > /dev/null 2>&1
apt-get install -y -qq wget > /dev/null 2>&1
wget -q https://mmseqs.com/latest/mmseqs-linux-avx2.tar.gz -O /tmp/mmseqs.tar.gz
tar xzf /tmp/mmseqs.tar.gz -C /tmp
export PATH="/tmp/mmseqs/bin:$PATH"
mmseqs version
echo "MMseqs2 installed successfully"

# Count input sequences
N_SEQS=$(grep -c "^>" "$INPUT_FASTA")
echo "Input sequences: $N_SEQS"

# Create MMseqs2 database
echo "--- Creating sequence database ---"
TMPDIR=$(mktemp -d)
mmseqs createdb "$INPUT_FASTA" "$TMPDIR/seqDB"

# Cluster at each identity level
for MINID in 0.9 0.5 0.3; do
    LABEL=$(echo "$MINID" | sed 's/0\.//')
    echo "--- Clustering at ${LABEL}0% identity ---"

    mmseqs cluster "$TMPDIR/seqDB" "$TMPDIR/clu_${LABEL}" "$TMPDIR/tmp_${LABEL}" \
        --min-seq-id "$MINID" \
        -c 0.8 \
        --cov-mode 0 \
        --threads 4 \
        2>&1 | tail -5

    # Extract cluster membership as TSV
    mmseqs createtsv "$TMPDIR/seqDB" "$TMPDIR/seqDB" "$TMPDIR/clu_${LABEL}" \
        "${OUTPUT_DIR}/clusters_${LABEL}0pct.tsv"

    # Count clusters
    N_CLUSTERS=$(cut -f1 "${OUTPUT_DIR}/clusters_${LABEL}0pct.tsv" | sort -u | wc -l)
    echo "  ${LABEL}0% identity: $N_CLUSTERS clusters from $N_SEQS sequences"
done

# Generate summary
echo "--- Summary ---" | tee "${OUTPUT_DIR}/clustering_summary.txt"
echo "Input sequences: $N_SEQS" | tee -a "${OUTPUT_DIR}/clustering_summary.txt"
for MINID in 90 50 30; do
    N=$(cut -f1 "${OUTPUT_DIR}/clusters_${MINID}pct.tsv" | sort -u | wc -l)
    echo "${MINID}% identity: $N clusters from $N_SEQS sequences" | tee -a "${OUTPUT_DIR}/clustering_summary.txt"
done

# Cluster size distributions
for MINID in 90 50 30; do
    echo "--- Cluster size distribution at ${MINID}% ---" >> "${OUTPUT_DIR}/clustering_summary.txt"
    cut -f1 "${OUTPUT_DIR}/clusters_${MINID}pct.tsv" | sort | uniq -c | sort -rn | \
        awk '{sizes[$1]++} END {for (s in sizes) print s, sizes[s]}' | sort -n | \
        tail -20 >> "${OUTPUT_DIR}/clustering_summary.txt"
done

echo "=== Done ==="
date
