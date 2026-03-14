#!/usr/bin/env python3
"""
Assess InterPro coverage across gene clusters and produce a gap report.

Reads outputs from scripts 03 and 04, produces a coverage report
showing how many gene clusters have InterPro results and at what quality.

Input:
  data/interpro_lookup/gene_cluster_accessions.tsv
  data/interpro_lookup/interpro_matches.tsv    (bulk matches)
  data/interpro_lookup/api_matches.tsv         (API matches, optional)
  data/interpro_lookup/api_no_results.tsv      (API misses, optional)
  data/interpro_lookup/bulk/entry.list         (InterPro entry descriptions)

Output:
  data/interpro_lookup/coverage_report.txt
  data/interpro_lookup/unmatched_clusters.tsv  (clusters needing InterProScan)

Usage:
  python data/interpro_lookup/scripts/05_assess_coverage.py
"""

import os
import sys
from collections import Counter, defaultdict

OUT_DIR = "data/interpro_lookup"
ACCESSIONS_FILE = os.path.join(OUT_DIR, "gene_cluster_accessions.tsv")
BULK_MATCHES = os.path.join(OUT_DIR, "interpro_matches.tsv")
API_MATCHES = os.path.join(OUT_DIR, "api_matches.tsv")
API_NO_RESULTS = os.path.join(OUT_DIR, "api_no_results.tsv")
ENTRY_LIST = os.path.join(OUT_DIR, "bulk", "entry.list")
REPORT_FILE = os.path.join(OUT_DIR, "coverage_report.txt")
UNMATCHED_FILE = os.path.join(OUT_DIR, "unmatched_clusters.tsv")


def load_entry_types(filepath):
    """Load InterPro entry types from entry.list."""
    types = {}
    if not os.path.exists(filepath):
        return types
    with open(filepath) as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) >= 2:
                types[parts[0]] = parts[1]  # IPR_id -> type (Family, Domain, etc)
    return types


def count_matched_clusters(filepath, gc_col_idx=0):
    """Count unique gene clusters from a match file."""
    clusters = set()
    if not os.path.exists(filepath):
        return clusters, Counter()

    ipr_counter = Counter()
    with open(filepath) as f:
        next(f)  # skip header
        for line in f:
            parts = line.strip().split("\t")
            if parts:
                clusters.add(parts[gc_col_idx])
                # Count IPR entries
                ipr_idx = 3 if filepath == BULK_MATCHES else 3
                if len(parts) > ipr_idx and parts[ipr_idx].startswith("IPR"):
                    ipr_counter[parts[ipr_idx]] += 1
    return clusters, ipr_counter


def load_all_clusters(filepath):
    """Load all gene cluster IDs and their accession status."""
    clusters = {}  # gc_id -> {'uniref100': acc, 'uniref90': acc, ...}
    with open(filepath) as f:
        header = f.readline().strip().split("\t")
        col_idx = {name: i for i, name in enumerate(header)}

        for line in f:
            parts = line.strip().split("\t")
            gc_id = parts[col_idx["gene_cluster_id"]]
            info = {}
            for col in ["uniref100_acc", "uniref90_acc", "uniref50_acc"]:
                idx = col_idx.get(col)
                if idx is not None and idx < len(parts):
                    val = parts[idx]
                    if val and val != "" and val != "None":
                        info[col] = val
            if "uniparc" in col_idx:
                idx = col_idx["uniparc"]
                if idx < len(parts) and parts[idx] and parts[idx] != "None":
                    info["uniparc"] = parts[idx]
            clusters[gc_id] = info

    return clusters


def main():
    if not os.path.exists(ACCESSIONS_FILE):
        print(f"ERROR: {ACCESSIONS_FILE} not found.")
        sys.exit(1)

    print("Loading data...")

    # All clusters
    all_clusters = load_all_clusters(ACCESSIONS_FILE)
    total = len(all_clusters)

    # Matched from bulk
    bulk_matched, bulk_ipr_counts = count_matched_clusters(BULK_MATCHES)

    # Matched from API
    api_matched, api_ipr_counts = count_matched_clusters(API_MATCHES, gc_col_idx=1)

    # API no-results
    api_no_results_accs = set()
    if os.path.exists(API_NO_RESULTS):
        with open(API_NO_RESULTS) as f:
            next(f)
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 2:
                    for gc_id in parts[1].split(","):
                        api_no_results_accs.add(gc_id.strip())

    # Combined
    all_matched = bulk_matched | api_matched
    all_ipr_counts = bulk_ipr_counts + api_ipr_counts

    # Classify clusters
    has_any_accession = {gc for gc, info in all_clusters.items() if info}
    no_accession = {gc for gc, info in all_clusters.items() if not info}
    unmatched = has_any_accession - all_matched - api_no_results_accs

    # Entry type breakdown
    entry_types = load_entry_types(ENTRY_LIST)
    type_counts = Counter()
    for ipr_id in all_ipr_counts:
        etype = entry_types.get(ipr_id, "Unknown")
        type_counts[etype] += all_ipr_counts[ipr_id]

    # Tier breakdown of matched clusters
    tier_counts = Counter()
    if os.path.exists(BULK_MATCHES):
        with open(BULK_MATCHES) as f:
            next(f)
            seen = set()
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 2:
                    key = (parts[0], parts[1])  # gc_id, tier
                    if key not in seen:
                        seen.add(key)
                        tier_counts[parts[1]] += 1

    # Top InterPro entries
    top_entries = all_ipr_counts.most_common(20)

    # Build report
    report = []
    report.append("=" * 70)
    report.append("InterPro Coverage Report for Pangenome Gene Clusters")
    report.append("=" * 70)
    report.append("")
    report.append(f"Total gene clusters:        {total:>12,}")
    report.append(f"With any UniRef accession:   {len(has_any_accession):>12,} "
                  f"({len(has_any_accession)/total*100:.1f}%)")
    report.append(f"Without any accession:       {len(no_accession):>12,} "
                  f"({len(no_accession)/total*100:.1f}%)")
    report.append("")
    report.append("─── InterPro Match Results ───")
    report.append("")
    report.append(f"Matched (bulk):              {len(bulk_matched):>12,} "
                  f"({len(bulk_matched)/total*100:.1f}%)")
    report.append(f"Matched (API):               {len(api_matched):>12,} "
                  f"({len(api_matched)/total*100:.1f}%)")
    report.append(f"Matched (total):             {len(all_matched):>12,} "
                  f"({len(all_matched)/total*100:.1f}%)")
    report.append(f"Confirmed no results (API):  {len(api_no_results_accs):>12,}")
    report.append(f"Not yet looked up:           {len(unmatched):>12,}")
    report.append(f"No accession (need IPS):     {len(no_accession):>12,}")
    report.append("")

    if tier_counts:
        report.append("─── Match Quality Tiers ───")
        report.append("")
        for tier in ["uniref100", "uniref90", "uniref50"]:
            n = tier_counts.get(tier, 0)
            report.append(f"  {tier}:  {n:>12,}")
        report.append("")

    if type_counts:
        report.append("─── InterPro Entry Types ───")
        report.append("")
        for etype, count in type_counts.most_common():
            report.append(f"  {etype:<20s}  {count:>12,}")
        report.append("")

    if top_entries:
        report.append("─── Top 20 InterPro Entries ───")
        report.append("")
        for ipr_id, count in top_entries:
            desc = entry_types.get(ipr_id, "")
            report.append(f"  {ipr_id}  {count:>10,}  {desc}")
        report.append("")

    report.append("─── Gap Analysis ───")
    report.append("")
    gap_total = len(no_accession) + len(unmatched)
    report.append(f"Need full InterProScan:      {gap_total:>12,} "
                  f"({gap_total/total*100:.1f}%)")
    report.append(f"  No accession at all:       {len(no_accession):>12,}")
    report.append(f"  Has accession, no match:   {len(unmatched):>12,}")
    report.append("")
    report.append("=" * 70)

    report_text = "\n".join(report)
    print(report_text)

    with open(REPORT_FILE, "w") as f:
        f.write(report_text + "\n")
    print(f"\nReport saved: {REPORT_FILE}")

    # Write unmatched clusters
    unmatched_all = no_accession | unmatched
    with open(UNMATCHED_FILE, "w") as f:
        f.write("gene_cluster_id\treason\tbest_accession\n")
        for gc_id in sorted(unmatched_all):
            info = all_clusters.get(gc_id, {})
            if not info:
                f.write(f"{gc_id}\tno_accession\t\n")
            else:
                best = (info.get("uniref100_acc") or info.get("uniref90_acc")
                        or info.get("uniref50_acc") or "")
                f.write(f"{gc_id}\tno_interpro_match\t{best}\n")

    print(f"Unmatched clusters: {UNMATCHED_FILE} ({len(unmatched_all):,} rows)")


if __name__ == "__main__":
    main()
