"""
Compute coverage of FB PaperBLAST (geneId, pmId) hit pairs by the merged
manuscript-summaries corpus. Optionally restricts to a gene-list file
(one orgId\tlocusId per line) — when given, reports coverage for that
subset only (e.g. the 1,762 reannotation set).

Outputs a summary to stderr; no parquet/tsv written.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"

HITS = PROJECT_DATA / "fb_paperblast_hit_papers.parquet"
SUMMARIES = PROJECT_DATA / "manuscript-summaries-merged.tsv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gene-list", help="Optional file with orgId\\tlocusId rows")
    args = parser.parse_args()

    hits = pd.read_parquet(HITS)
    hits["pmId"] = hits["pmId"].astype(str)
    print(f"Total FB PaperBLAST hits: {len(hits):,}", file=sys.stderr)
    print(f"  unique (geneId, pmId):  {len(hits[['geneId','pmId']].drop_duplicates()):,}", file=sys.stderr)
    print(f"  unique pmIds:           {hits['pmId'].nunique():,}", file=sys.stderr)
    print(f"  unique FB loci:         {len(hits[['orgId','locusId']].drop_duplicates()):,}", file=sys.stderr)

    if args.gene_list:
        keys = set()
        with open(args.gene_list) as fh:
            for line in fh:
                parts = line.rstrip().split("\t")
                if len(parts) >= 2:
                    keys.add((parts[0], parts[1]))
        print(f"\nGene-list filter: {len(keys):,} genes", file=sys.stderr)
        sub = hits[hits.apply(lambda r: (r["orgId"], r["locusId"]) in keys, axis=1)].copy()
        print(f"  hits in subset:        {len(sub):,}", file=sys.stderr)
        print(f"  unique (geneId,pmId):  {len(sub[['geneId','pmId']].drop_duplicates()):,}", file=sys.stderr)
        hits = sub

    print(f"\nLoading merged summaries...", file=sys.stderr)
    have = set()
    have_nonnull = set()
    with open(SUMMARIES) as fh:
        next(fh, None)
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            mid, _, gid = parts[0], parts[1], parts[2]
            summ = "\t".join(parts[3:])
            have.add((gid, mid))
            if summ.strip().lower() not in ("null", ""):
                have_nonnull.add((gid, mid))
    print(f"  merged corpus rows: {len(have):,}  (non-null: {len(have_nonnull):,})", file=sys.stderr)

    pairs = hits[["geneId", "pmId"]].drop_duplicates().itertuples(index=False, name=None)
    n_total = n_in = n_nonnull = 0
    for gid, pmid in pairs:
        n_total += 1
        if (gid, pmid) in have:
            n_in += 1
            if (gid, pmid) in have_nonnull:
                n_nonnull += 1

    print(f"\n=== Coverage ===", file=sys.stderr)
    print(f"  pairs total:                 {n_total:,}", file=sys.stderr)
    print(f"  in merged corpus (any):      {n_in:,}  ({100*n_in/n_total:.1f}%)", file=sys.stderr)
    print(f"  in merged corpus (non-null): {n_nonnull:,}  ({100*n_nonnull/n_total:.1f}%)", file=sys.stderr)
    print(f"  gap (would need run):        {n_total - n_in:,}  ({100*(n_total-n_in)/n_total:.1f}%)", file=sys.stderr)


if __name__ == "__main__":
    main()
