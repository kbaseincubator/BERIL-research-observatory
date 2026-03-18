#!/usr/bin/env python3
"""
Transform InterProScan 15-column TSV results into 3 normalized tables.

Reads 13,254 split TSV files from InterProScan output and produces:
  1. interproscan_domains — one row per protein × analysis hit (core domain data)
  2. interproscan_go — deduplicated GO term assignments per protein
  3. interproscan_pathways — deduplicated pathway assignments per protein

Usage:
  # Run directly (small test)
  python 09_transform_results.py /pscratch/sd/p/psdehal/interproscan/results/

  # Submit as SLURM job (production)
  sbatch --account=amsc002 --qos=shared --cpus-per-task=16 --mem=8G --time=02:00:00 \
    --wrap="python scripts/09_transform_results.py /pscratch/sd/p/psdehal/interproscan/results/ --workers 16"
"""

import argparse
import os
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

RESULTS_DIR_DEFAULT = "/pscratch/sd/p/psdehal/interproscan/results"
OUTPUT_DIR_DEFAULT = "/pscratch/sd/p/psdehal/interproscan/tables"

DOMAINS_HEADER = "\t".join([
    "gene_cluster_id", "md5", "seq_len", "analysis",
    "signature_acc", "signature_desc", "start", "stop",
    "score", "ipr_acc", "ipr_desc",
]) + "\n"

GO_HEADER = "\t".join([
    "gene_cluster_id", "go_id", "go_source", "n_supporting_analyses",
]) + "\n"

PATHWAYS_HEADER = "\t".join([
    "gene_cluster_id", "pathway_db", "pathway_id", "n_supporting_analyses",
]) + "\n"


def normalize_reactome_id(rid):
    """Strip species prefix from Reactome IDs: R-HSA-350562 → 350562.

    Reactome maps the same pathway across 16+ eukaryotic species, inflating
    the pathway table ~15x. For bacterial proteins these species-specific
    entries are not meaningful; normalizing to the base pathway ID deduplicates
    them. MetaCyc/KEGG IDs are returned unchanged.
    """
    # Reactome format: R-{species}-{number} e.g. R-HSA-350562
    parts = rid.split("-", 2)
    if len(parts) == 3 and parts[0] == "R":
        return parts[2]
    return rid


def process_split(args):
    """Process a single split TSV file, producing 3 output files."""
    input_path, domains_dir, go_dir, pathways_dir, norm_reactome, include_reactome = args
    split_name = os.path.basename(input_path)

    domains_rows = 0
    go_rows = 0
    pathways_rows = 0

    # Per-file dedup for GO and pathways: (gene_cluster_id, go_id, source) -> count
    go_dedup = defaultdict(int)
    pw_dedup = defaultdict(int)

    domains_path = os.path.join(domains_dir, split_name)
    go_path = os.path.join(go_dir, split_name)
    pathways_path = os.path.join(pathways_dir, split_name)

    with open(input_path) as fin, open(domains_path, "w") as fdom:
        for line in fin:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t")
            # Pad to 15 columns
            while len(parts) < 15:
                parts.append("")

            gene_cluster_id = parts[0]
            md5 = parts[1]
            seq_len = parts[2]
            analysis = parts[3]
            sig_acc = parts[4]
            sig_desc = parts[5]
            start = parts[6]
            stop = parts[7]
            score = parts[8]
            # parts[9] = status (always "T"), parts[10] = date — skip
            ipr_acc = parts[11] if parts[11] != "-" else ""
            ipr_desc = parts[12] if parts[12] != "-" else ""
            go_terms = parts[13]
            pathways = parts[14]

            # Write domain row
            fdom.write("\t".join([
                gene_cluster_id, md5, seq_len, analysis,
                sig_acc, sig_desc, start, stop,
                score, ipr_acc, ipr_desc,
            ]) + "\n")
            domains_rows += 1

            # Parse GO terms: GO:0005515(InterPro)|GO:0046933(PANTHER)
            if go_terms and go_terms != "-":
                for entry in go_terms.split("|"):
                    entry = entry.strip()
                    if not entry:
                        continue
                    # Format: GO:NNNNNNN(Source)
                    paren = entry.rfind("(")
                    if paren > 0 and entry.endswith(")"):
                        go_id = entry[:paren]
                        go_source = entry[paren + 1:-1]
                    else:
                        go_id = entry
                        go_source = ""
                    go_dedup[(gene_cluster_id, go_id, go_source)] += 1

            # Parse pathways: MetaCyc:PWY-2941|Reactome:R-HSA-209905
            if pathways and pathways != "-":
                for entry in pathways.split("|"):
                    entry = entry.strip()
                    if not entry:
                        continue
                    # Split on first colon: DB:ID (ID may contain colons)
                    colon = entry.find(":")
                    if colon > 0:
                        pw_db = entry[:colon]
                        pw_id = entry[colon + 1:]
                    else:
                        pw_db = entry
                        pw_id = ""
                    # Skip Reactome unless explicitly requested
                    if pw_db == "Reactome" and not include_reactome:
                        continue
                    # Normalize Reactome IDs to strip species prefix
                    if norm_reactome and pw_db == "Reactome":
                        pw_id = normalize_reactome_id(pw_id)
                    pw_dedup[(gene_cluster_id, pw_db, pw_id)] += 1

    # Write deduplicated GO file
    with open(go_path, "w") as fgo:
        for (gid, go_id, go_source), count in sorted(go_dedup.items()):
            fgo.write(f"{gid}\t{go_id}\t{go_source}\t{count}\n")
            go_rows += 1

    # Write deduplicated pathways file
    with open(pathways_path, "w") as fpw:
        for (gid, pw_db, pw_id), count in sorted(pw_dedup.items()):
            fpw.write(f"{gid}\t{pw_db}\t{pw_id}\t{count}\n")
            pathways_rows += 1

    return split_name, domains_rows, go_rows, pathways_rows


def main():
    parser = argparse.ArgumentParser(
        description="Transform InterProScan TSV into 3 normalized tables")
    parser.add_argument("results_dir", nargs="?", default=RESULTS_DIR_DEFAULT,
                        help="Directory with split_NNNNN.tsv files")
    parser.add_argument("--output-dir", default=OUTPUT_DIR_DEFAULT,
                        help="Output directory for transformed tables")
    parser.add_argument("--workers", type=int, default=8,
                        help="Number of parallel workers")
    parser.add_argument("--limit", type=int, default=0,
                        help="Process only first N splits (0 = all, for testing)")
    parser.add_argument("--include-reactome", action="store_true",
                        help="Include Reactome pathways (eukaryotic, ~12B extra rows). "
                             "Default: exclude Reactome, keep MetaCyc/KEGG only.")
    parser.add_argument("--keep-reactome-species", action="store_true",
                        help="Keep species-specific Reactome IDs (default: normalize to base ID). "
                             "Only relevant with --include-reactome.")
    args = parser.parse_args()

    results_path = Path(args.results_dir)
    split_files = sorted(results_path.glob("split_*.tsv"))
    if not split_files:
        print(f"No split_*.tsv files found in {args.results_dir}")
        sys.exit(1)

    if args.limit > 0:
        split_files = split_files[:args.limit]

    # Create output directories
    domains_dir = os.path.join(args.output_dir, "domains")
    go_dir = os.path.join(args.output_dir, "go")
    pathways_dir = os.path.join(args.output_dir, "pathways")
    for d in [domains_dir, go_dir, pathways_dir]:
        os.makedirs(d, exist_ok=True)

    print(f"Input:   {len(split_files)} split files in {args.results_dir}")
    print(f"Output:  {args.output_dir}/{{domains,go,pathways}}/")
    print(f"Workers: {args.workers}")
    print()

    include_reactome = args.include_reactome
    norm_reactome = not args.keep_reactome_species
    if not include_reactome:
        print("Pathways: excluding Reactome (eukaryotic, not relevant for bacteria)")
        print("          Use --include-reactome to include (~12B extra rows)")
    elif norm_reactome:
        print("Reactome IDs: normalizing (strip species prefix for dedup)")
    else:
        print("Reactome IDs: keeping species-specific (WARNING: ~15x more pathway rows)")
    print()

    # Build work items
    work = [
        (str(f), domains_dir, go_dir, pathways_dir, norm_reactome, include_reactome)
        for f in split_files
    ]

    total_domains = 0
    total_go = 0
    total_pathways = 0
    done = 0

    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(process_split, w): w[0] for w in work}
        for future in as_completed(futures):
            split_name, d, g, p = future.result()
            total_domains += d
            total_go += g
            total_pathways += p
            done += 1
            if done % 500 == 0 or done == len(split_files):
                print(f"  [{done:>6}/{len(split_files)}] "
                      f"domains={total_domains:>12,}  "
                      f"go={total_go:>10,}  "
                      f"pathways={total_pathways:>10,}")

    print(f"\nTransform complete:")
    print(f"  Domains:  {total_domains:>14,} rows → {domains_dir}/")
    print(f"  GO:       {total_go:>14,} rows → {go_dir}/")
    print(f"  Pathways: {total_pathways:>14,} rows → {pathways_dir}/")

    # Write header files (will be prepended during concatenation)
    with open(os.path.join(args.output_dir, "domains_header.tsv"), "w") as f:
        f.write(DOMAINS_HEADER)
    with open(os.path.join(args.output_dir, "go_header.tsv"), "w") as f:
        f.write(GO_HEADER)
    with open(os.path.join(args.output_dir, "pathways_header.tsv"), "w") as f:
        f.write(PATHWAYS_HEADER)

    print(f"\nNext: concatenate and compress for upload:")
    print(f"  cat {args.output_dir}/domains_header.tsv {domains_dir}/split_*.tsv | pigz > interproscan_domains.tsv.gz")
    print(f"  cat {args.output_dir}/go_header.tsv {go_dir}/split_*.tsv | pigz > interproscan_go.tsv.gz")
    print(f"  cat {args.output_dir}/pathways_header.tsv {pathways_dir}/split_*.tsv | pigz > interproscan_pathways.tsv.gz")


if __name__ == "__main__":
    main()
