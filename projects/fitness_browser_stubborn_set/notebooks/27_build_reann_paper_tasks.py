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

    # Papers covered by ANY existing summary corpus (paper-level, not per-gene).
    # Rationale: if we already have a summary of paper P for some homolog X,
    # the existing summary still gives the agent useful paper-level context
    # for any other homolog Y discussed in the same paper. We re-summarize
    # only papers with zero coverage.
    have_pmids: set[str] = set()
    with open(MERGED) as fh:
        next(fh, None)
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            mid = parts[0]
            summ = "\t".join(parts[3:])
            # Only count as "covered" if at least one row for this pmId is non-null
            if summ.strip().lower() not in ("null", ""):
                have_pmids.add(mid)
    print(f"Merged corpus papers with ≥1 non-null summary: {len(have_pmids):,}", file=sys.stderr)

    hits = pd.read_parquet(HITS)
    hits["pmId"] = hits["pmId"].astype(str)
    sub = hits[hits.apply(lambda r: (r["orgId"], r["locusId"]) in keys, axis=1)].copy()
    print(f"PaperBLAST hits joined to reann: {len(sub):,}", file=sys.stderr)

    # Drop papers we already have
    sub = sub[sub["pmId"].astype(str).str.len() > 0].copy()
    sub["covered"] = sub["pmId"].isin(have_pmids)
    n_unique_papers = sub["pmId"].nunique()
    n_covered_papers = sub[sub["covered"]]["pmId"].nunique()
    n_uncovered_papers = sub[~sub["covered"]]["pmId"].nunique()
    print(f"  unique papers in reann hits: {n_unique_papers:,}", file=sys.stderr)
    print(f"    already-covered papers:    {n_covered_papers:,}", file=sys.stderr)
    print(f"    papers needing summary:    {n_uncovered_papers:,}", file=sys.stderr)
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
