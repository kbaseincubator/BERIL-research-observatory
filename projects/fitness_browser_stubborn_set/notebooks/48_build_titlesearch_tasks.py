"""
Build summarization tasks for the pmids resolved via title search.

For each (homolog, resolved_pmid) pair from the None-pmid PaperBLAST hits
where the title matches a resolved entry in title_resolutions_relaxed.tsv,
build a tasks.jsonl entry. Output goes into a fresh
`data/codex_summaries_titlesearch/` directory which the existing summarization
pipeline (07/08/09) can consume via SUM_DIR env var.

Output:
  data/codex_summaries_titlesearch/tasks.jsonl
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
TS_DIR = PROJECT_DATA / "codex_summaries_titlesearch"
RESOLUTIONS = TS_DIR / "title_resolutions_relaxed.tsv"
OUT_TASKS = TS_DIR / "tasks.jsonl"


def clean_title(t: str) -> str:
    t = re.sub(r"<[^>]+>", "", t or "")
    t = re.sub(r"&[a-z]+;", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def main() -> None:
    # Load resolutions: title -> resolved_pmid
    title_to_pmid: dict[str, str] = {}
    pmid_to_meta: dict[str, dict] = {}
    with open(RESOLUTIONS) as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            pmid = r.get("resolved_pmid") or ""
            title = clean_title(r["original_title"])
            if pmid and title:
                title_to_pmid[title] = pmid
                if pmid not in pmid_to_meta:
                    pmid_to_meta[pmid] = {
                        "title": title,
                        "year": int(r["year"]) if r.get("year") and r["year"].isdigit() else None,
                        "journal": r.get("found_journal") or r.get("journal") or "",
                    }
    print(f"resolved title→pmid mappings: {len(title_to_pmid)}", file=sys.stderr)

    # Load training-set keys
    training_keys = set()
    for fname in (
        "human_validated.jsonl",
        "llm_vs_human_disagreements.jsonl",
        "negatives.jsonl",
        "positives.jsonl",
    ):
        with open(PROJECT_DATA / "training_set" / fname) as fh:
            for line in fh:
                r = json.loads(line)
                training_keys.add((r["orgId"], r["locusId"]))

    # Find None-pmid hits whose titles are now resolved
    hits = pd.read_parquet(PROJECT_DATA / "fb_paperblast_hit_papers.parquet")
    hits["pmId"] = hits["pmId"].astype(str)
    none_hits = hits[(hits["pmId"] == "None") & hits["geneId"].notna() & (hits["geneId"].astype(str) != "None")].copy()
    none_hits = none_hits[none_hits.apply(lambda r: (r["orgId"], r["locusId"]) in training_keys, axis=1)]
    none_hits["title_clean"] = none_hits["title"].fillna("").apply(clean_title)
    none_hits["resolved_pmid"] = none_hits["title_clean"].map(title_to_pmid)
    matched = none_hits[none_hits["resolved_pmid"].notna()]
    print(f"None-pmid hits with resolved titles: {len(matched):,}", file=sys.stderr)

    # Group by resolved pmid -> collect homologs
    by_pmid: dict[str, dict] = {}
    for _, r in matched.iterrows():
        pmid = r["resolved_pmid"]
        if pmid not in by_pmid:
            meta = pmid_to_meta[pmid]
            by_pmid[pmid] = {
                "pmId": pmid,
                "title": meta["title"],
                "year": meta["year"],
                "journal": meta["journal"],
                "gene_identifiers": [],
                "_seen_geneids": set(),
            }
        gid = r["geneId"]
        if gid not in by_pmid[pmid]["_seen_geneids"]:
            by_pmid[pmid]["gene_identifiers"].append({
                "geneId": gid,
                "pb_organism": r.get("pb_organism") or "",
                "pb_desc": r.get("pb_desc") or "",
            })
            by_pmid[pmid]["_seen_geneids"].add(gid)

    TS_DIR.mkdir(parents=True, exist_ok=True)
    n_papers = n_pairs = 0
    with open(OUT_TASKS, "w") as fh:
        for pmid, t in by_pmid.items():
            t.pop("_seen_geneids", None)
            fh.write(json.dumps(t, ensure_ascii=False) + "\n")
            n_papers += 1
            n_pairs += len(t["gene_identifiers"])
    print(f"\nWrote {OUT_TASKS}", file=sys.stderr)
    print(f"  papers: {n_papers}", file=sys.stderr)
    print(f"  (homolog, paper) pairs: {n_pairs}", file=sys.stderr)


if __name__ == "__main__":
    main()
