#!/usr/bin/env python3
"""
Match gene cluster accessions against InterPro bulk data (protein2ipr.dat.gz).

Streams through the 16GB compressed protein2ipr.dat.gz file and extracts
InterPro results for gene clusters whose UniProt accessions match.

Prioritizes matches by quality:
  1. UniRef100 accessions (exact sequence match)
  2. UniRef90 accessions (≥90% identity)
  3. UniRef50 accessions (≥50% identity)

Input:
  data/interpro_lookup/gene_cluster_accessions.tsv  (from script 01)
  data/interpro_lookup/bulk/protein2ipr.dat.gz      (from script 02)

Output:
  data/interpro_lookup/interpro_matches.tsv
  data/interpro_lookup/match_summary.tsv

Usage:
  python data/interpro_lookup/scripts/03_match_bulk.py
  python data/interpro_lookup/scripts/03_match_bulk.py --resume  # resume from checkpoint
"""

import argparse
import gzip
import json
import os
import sys
import time
from collections import defaultdict

OUT_DIR = "data/interpro_lookup"
ACCESSIONS_FILE = os.path.join(OUT_DIR, "gene_cluster_accessions.tsv")
BULK_FILE = os.path.join(OUT_DIR, "bulk", "protein2ipr.dat.gz")
OUT_FILE = os.path.join(OUT_DIR, "interpro_matches.tsv")
SUMMARY_FILE = os.path.join(OUT_DIR, "match_summary.tsv")
CHECKPOINT_FILE = os.path.join(OUT_DIR, "checkpoints", "bulk_match_checkpoint.json")

# Checkpoint every N lines of the bulk file
CHECKPOINT_INTERVAL = 50_000_000  # ~50M lines


def load_accession_index(filepath):
    """Load gene cluster accessions into lookup dictionaries.

    Returns three dicts (one per tier), each mapping UniProt accession
    to a list of gene_cluster_ids. A cluster appears in the highest-priority
    tier it has an accession for.
    """
    print(f"Loading accessions from {filepath}...")
    t0 = time.time()

    # accession -> set of (gene_cluster_id, tier)
    acc_to_clusters = defaultdict(set)
    # Track which clusters have accessions at each tier
    cluster_tiers = {}  # gene_cluster_id -> best tier found
    total_clusters = 0

    with open(filepath) as f:
        header = f.readline().strip().split("\t")
        col_idx = {name: i for i, name in enumerate(header)}

        for line in f:
            parts = line.strip().split("\t")
            total_clusters += 1
            gc_id = parts[col_idx["gene_cluster_id"]]

            # Check each tier (best first)
            for tier, col in [("uniref100", "uniref100_acc"),
                              ("uniref90", "uniref90_acc"),
                              ("uniref50", "uniref50_acc")]:
                idx = col_idx.get(col)
                if idx is not None and idx < len(parts):
                    acc = parts[idx]
                    if acc and acc != "" and acc != "None":
                        acc_to_clusters[acc].add((gc_id, tier))
                        # Track best tier for this cluster
                        if gc_id not in cluster_tiers:
                            cluster_tiers[gc_id] = tier

    unique_accessions = len(acc_to_clusters)
    elapsed = time.time() - t0
    print(f"  Loaded {total_clusters:,} clusters")
    print(f"  {unique_accessions:,} unique UniProt accessions to look up")
    print(f"  Clusters with accessions: {len(cluster_tiers):,}")
    print(f"  Loaded in {elapsed:.1f}s")

    # Memory estimate
    mem_mb = sys.getsizeof(acc_to_clusters) / 1024 / 1024
    print(f"  Index size: ~{mem_mb:.0f} MB (approximate)")

    return acc_to_clusters, cluster_tiers, total_clusters


def stream_match(acc_to_clusters, resume_line=0):
    """Stream through protein2ipr.dat.gz and match accessions.

    protein2ipr.dat format (tab-separated):
      UniProt_acc  IPR_id  IPR_desc  source_db  source_acc  start  stop

    Yields (accession, ipr_id, ipr_desc, source_db, source_acc, start, stop)
    for matching accessions.
    """
    print(f"\nStreaming through {BULK_FILE}...")
    if resume_line > 0:
        print(f"  Resuming from line {resume_line:,}")

    # Convert accessions to a frozenset for O(1) lookup
    acc_set = frozenset(acc_to_clusters.keys())
    print(f"  Looking for {len(acc_set):,} accessions")

    t0 = time.time()
    lines_read = 0
    matches = 0
    last_report = t0

    with gzip.open(BULK_FILE, "rt", encoding="utf-8") as f:
        # Skip to resume point
        if resume_line > 0:
            print(f"  Skipping to line {resume_line:,}...")
            for _ in range(resume_line):
                next(f)
                lines_read += 1

        for line in f:
            lines_read += 1
            parts = line.rstrip("\n").split("\t")

            if len(parts) < 6:
                continue

            accession = parts[0]
            if accession in acc_set:
                matches += 1
                yield (
                    accession,
                    parts[1],                    # IPR id
                    parts[2] if len(parts) > 2 else "",  # IPR description
                    parts[3] if len(parts) > 3 else "",  # source db
                    parts[4] if len(parts) > 4 else "",  # source accession
                    parts[5] if len(parts) > 5 else "",  # start
                    parts[6] if len(parts) > 6 else "",  # stop
                )

            # Progress reporting every 60 seconds
            now = time.time()
            if now - last_report > 60:
                rate = lines_read / (now - t0)
                print(f"  {lines_read:,} lines | {matches:,} matches | "
                      f"{rate:,.0f} lines/sec")
                last_report = now

            # Checkpoint
            if lines_read % CHECKPOINT_INTERVAL == 0:
                _save_checkpoint(lines_read, matches)

    elapsed = time.time() - t0
    rate = lines_read / elapsed if elapsed > 0 else 0
    print(f"\n  Finished: {lines_read:,} lines, {matches:,} matches in {elapsed:.0f}s "
          f"({rate:,.0f} lines/sec)")

    return matches


def _save_checkpoint(lines_read, matches):
    """Save progress checkpoint."""
    os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({
            "lines_read": lines_read,
            "matches": matches,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }, f)


def _load_checkpoint():
    """Load checkpoint if exists."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return None


def main():
    parser = argparse.ArgumentParser(description="Match accessions against InterPro bulk data")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--dry-run", action="store_true", help="Just load index and report stats")
    args = parser.parse_args()

    # Validate inputs
    if not os.path.exists(ACCESSIONS_FILE):
        print(f"ERROR: {ACCESSIONS_FILE} not found. Run 01_extract_identifiers.py first.")
        sys.exit(1)
    if not os.path.exists(BULK_FILE):
        print(f"ERROR: {BULK_FILE} not found. Run 02_download_interpro_bulk.sh first.")
        sys.exit(1)

    # Load accession index
    acc_to_clusters, cluster_tiers, total_clusters = load_accession_index(ACCESSIONS_FILE)

    if args.dry_run:
        print("\n=== Dry run — stats only ===")
        tier_counts = defaultdict(int)
        for tier in cluster_tiers.values():
            tier_counts[tier] += 1
        for tier in ["uniref100", "uniref90", "uniref50"]:
            print(f"  {tier}: {tier_counts.get(tier, 0):,} clusters")
        no_acc = total_clusters - len(cluster_tiers)
        print(f"  No accession: {no_acc:,} clusters")
        return

    # Resume point
    resume_line = 0
    if args.resume:
        checkpoint = _load_checkpoint()
        if checkpoint:
            resume_line = checkpoint["lines_read"]
            print(f"Resuming from checkpoint: line {resume_line:,}")

    os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)

    # Stream and match
    matched_accessions = set()
    write_mode = "a" if resume_line > 0 else "w"

    with open(OUT_FILE, write_mode) as out:
        if write_mode == "w":
            out.write("gene_cluster_id\ttier\tuniprot_acc\tipr_id\tipr_desc\t"
                       "source_db\tsource_acc\tstart\tstop\n")

        for (acc, ipr_id, ipr_desc, src_db, src_acc, start, stop) in \
                stream_match(acc_to_clusters, resume_line):

            matched_accessions.add(acc)

            # Write one row per (gene_cluster, InterPro match)
            for gc_id, tier in acc_to_clusters[acc]:
                out.write(f"{gc_id}\t{tier}\t{acc}\t{ipr_id}\t{ipr_desc}\t"
                          f"{src_db}\t{src_acc}\t{start}\t{stop}\n")

    # Summary
    matched_clusters = set()
    tier_matched = defaultdict(int)
    for acc in matched_accessions:
        for gc_id, tier in acc_to_clusters[acc]:
            matched_clusters.add(gc_id)
            tier_matched[tier] += 1

    unmatched = total_clusters - len(matched_clusters)

    print(f"\n=== Match Summary ===")
    print(f"Total clusters:     {total_clusters:,}")
    print(f"Matched (any tier): {len(matched_clusters):,} "
          f"({len(matched_clusters)/total_clusters*100:.1f}%)")
    for tier in ["uniref100", "uniref90", "uniref50"]:
        print(f"  via {tier}:     {tier_matched.get(tier, 0):,}")
    print(f"Unmatched:          {unmatched:,} ({unmatched/total_clusters*100:.1f}%)")
    print(f"Output: {OUT_FILE}")

    # Write summary
    with open(SUMMARY_FILE, "w") as f:
        f.write("metric\tvalue\n")
        f.write(f"total_clusters\t{total_clusters}\n")
        f.write(f"matched_clusters\t{len(matched_clusters)}\n")
        f.write(f"matched_pct\t{len(matched_clusters)/total_clusters*100:.2f}\n")
        f.write(f"matched_accessions\t{len(matched_accessions)}\n")
        for tier in ["uniref100", "uniref90", "uniref50"]:
            f.write(f"matched_via_{tier}\t{tier_matched.get(tier, 0)}\n")
        f.write(f"unmatched_clusters\t{unmatched}\n")
        f.write(f"unmatched_pct\t{unmatched/total_clusters*100:.2f}\n")

    # Clean up checkpoint on success
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)

    print(f"\nSummary: {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
