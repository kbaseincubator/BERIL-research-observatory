"""
Build per-paper task list for the positive (high-confidence already_correctly_named) set.

Reads positive_sample_500.jsonl, joins with PaperBLAST DIAMOND hits, and writes
data/codex_summaries_positive/tasks.jsonl listing each unique pmId with its
gene_identifiers from the positive set.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
DEFAULT_SAMPLE = PROJECT_DATA / "positive_sample_500.jsonl"
DEFAULT_HITS = PROJECT_DATA / "fb_paperblast_hit_papers.parquet"
OUT_DIR = PROJECT_DATA / "codex_summaries_positive"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-file", default=str(DEFAULT_SAMPLE))
    parser.add_argument("--hits-file", default=str(DEFAULT_HITS))
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    keys = set()
    with open(args.sample_file) as fh:
        for line in fh:
            r = json.loads(line)
            keys.add((r["orgId"], r["locusId"]))
    print(f"Loaded {len(keys)} positive-set genes", file=sys.stderr)

    hits = pd.read_parquet(args.hits_file)
    sub = hits[hits.apply(lambda r: (r["orgId"], r["locusId"]) in keys, axis=1)].copy()
    sub["pmId"] = sub["pmId"].astype(str)
    sub = sub[sub["pmId"].str.len() > 0].copy()
    print(f"PaperBLAST hits: {len(sub):,} rows for {sub.groupby(['orgId','locusId']).ngroups} genes", file=sys.stderr)

    grouped = sub.groupby("pmId")
    print(f"Unique papers: {grouped.ngroups:,}", file=sys.stderr)

    out_path = OUT_DIR / "tasks.jsonl"
    with open(out_path, "w") as fh:
        for pmId, g in grouped:
            gene_rows = (
                g[["geneId", "pb_desc", "pb_organism"]]
                .drop_duplicates(subset=["geneId"])
                .to_dict(orient="records")
            )
            row = {
                "pmId": pmId,
                "title": g.iloc[0].get("title", "") or "",
                "year": (int(g.iloc[0]["year"]) if pd.notna(g.iloc[0].get("year")) else None),
                "journal": g.iloc[0].get("journal", "") or "",
                "gene_identifiers": gene_rows,
            }
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
