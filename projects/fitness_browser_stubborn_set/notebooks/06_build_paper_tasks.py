"""
Build per-paper task list for Codex summarization.

For each unique pmId in the recalcitrant set's PaperBLAST hits, list the
PaperBLAST gene_identifiers (geneIds) it should summarize.

Output: data/codex_summaries/tasks.jsonl, one row per paper:
  {"pmId": "...", "title": "...", "year": ...,
   "gene_identifiers": [{"geneId": "...", "pb_desc": "...", "pb_organism": "..."}]}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
DEFAULT_VERDICTS = PROJECT_DATA / "random_sample_verdicts.jsonl"
DEFAULT_HITS = PROJECT_DATA / "fb_paperblast_hit_papers.parquet"
OUT_DIR = PROJECT_DATA / "codex_summaries"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verdicts-file", default=str(DEFAULT_VERDICTS))
    parser.add_argument("--hits-file", default=str(DEFAULT_HITS))
    parser.add_argument("--verdict", default="recalcitrant")
    args = parser.parse_args()

    verdicts_path = Path(args.verdicts_file)
    hits_path = Path(args.hits_file)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    keys = set()
    with open(verdicts_path) as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("verdict") == args.verdict:
                keys.add((r["orgId"], r["locusId"]))
    print(f"Loaded {len(keys)} {args.verdict} (orgId, locusId) keys", file=sys.stderr)

    hits = pd.read_parquet(hits_path)
    mask = hits.apply(lambda r: (r["orgId"], r["locusId"]) in keys, axis=1)
    sub = hits[mask].copy()
    print(f"Filtered hits: {len(sub):,} rows for {sub.geneId.nunique():,} unique geneIds", file=sys.stderr)

    # Group by pmId, collect unique geneIds with their descriptions
    sub = sub[sub["pmId"].astype(str).str.len() > 0].copy()
    sub["pmId"] = sub["pmId"].astype(str)
    grouped = sub.groupby("pmId")
    print(f"Unique papers: {grouped.ngroups:,}", file=sys.stderr)

    out_path = OUT_DIR / "tasks.jsonl"
    with open(out_path, "w") as fh:
        for pmId, g in grouped:
            # Collapse to unique geneIds within this paper
            gene_rows = (
                g[["geneId", "pb_desc", "pb_organism"]]
                .drop_duplicates(subset=["geneId"])
                .to_dict(orient="records")
            )
            title = g.iloc[0].get("title", "") or ""
            journal = g.iloc[0].get("journal", "") or ""
            year = g.iloc[0].get("year", None)
            try:
                year = int(year) if year is not None and not pd.isna(year) else None
            except Exception:
                year = None
            row = {
                "pmId": pmId,
                "title": title,
                "year": year,
                "journal": journal,
                "gene_identifiers": gene_rows,
            }
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
