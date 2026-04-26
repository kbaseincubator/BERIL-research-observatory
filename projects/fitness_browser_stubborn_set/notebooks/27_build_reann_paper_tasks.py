"""
Build per-paper Codex summarization tasks for the reannotation calibration set.

Per-paper task lists only the (geneId) entries NOT yet covered by the merged
manuscript-summaries corpus, so we don't re-summarize papers we already have.

Output:
  data/codex_summaries_reann/tasks.jsonl
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"

REANN = PROJECT_DATA / "reannotation_set.parquet"
HITS = PROJECT_DATA / "fb_paperblast_hit_papers.parquet"
MERGED = PROJECT_DATA / "manuscript-summaries-merged.tsv"
OUT_DIR = PROJECT_DATA / "codex_summaries_reann"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    reann = pd.read_parquet(REANN).dropna(subset=["orgId", "locusId"])
    keys = set(zip(reann["orgId"], reann["locusId"]))
    print(f"Reannotation genes: {len(keys)}", file=sys.stderr)

    # Already-covered (geneId, pmId) pairs
    have: set[tuple[str, str]] = set()
    with open(MERGED) as fh:
        next(fh, None)
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            mid, _, gid = parts[0], parts[1], parts[2]
            have.add((gid, mid))
    print(f"Merged corpus pairs: {len(have):,}", file=sys.stderr)

    hits = pd.read_parquet(HITS)
    hits["pmId"] = hits["pmId"].astype(str)
    sub = hits[hits.apply(lambda r: (r["orgId"], r["locusId"]) in keys, axis=1)].copy()
    print(f"PaperBLAST hits joined to reann: {len(sub):,}", file=sys.stderr)

    # Drop pairs we already have
    sub["covered"] = sub.apply(lambda r: (r["geneId"], r["pmId"]) in have, axis=1)
    print(f"  already covered: {sub['covered'].sum():,}", file=sys.stderr)
    print(f"  to summarize:    {(~sub['covered']).sum():,}", file=sys.stderr)
    sub = sub[~sub["covered"]].copy()

    # Group by pmId, collect unique geneIds
    grouped = sub.groupby("pmId")
    print(f"Unique papers needing summarization: {grouped.ngroups:,}", file=sys.stderr)

    out_path = OUT_DIR / "tasks.jsonl"
    with open(out_path, "w") as out:
        for pmId, g in grouped:
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
            out.write(json.dumps({
                "pmId": pmId,
                "title": title,
                "year": year,
                "journal": journal,
                "gene_identifiers": gene_rows,
            }, ensure_ascii=False) + "\n")
    print(f"Wrote {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
