"""
Resolve PaperBLAST 'None' pmId citations to actual PMIDs by title search.

Many PaperBLAST hits have `pmId = None` because the upstream bibliographic
metadata didn't include a PubMed ID. We have the title + journal + year for
these hits. Searching Europe PMC by title typically finds the PMID, after
which the paper can be fetched + summarized via the existing pipelines.

Output:
  data/codex_summaries_titlesearch/title_resolutions.tsv
    columns: title_hash, original_title, resolved_pmid, source, journal_match
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
OUT_DIR = PROJECT_DATA / "codex_summaries_titlesearch"
OUT_DIR.mkdir(parents=True, exist_ok=True)
RESOLUTIONS = OUT_DIR / "title_resolutions.tsv"

NCBI_TOOL = "kbase-fb-stubborn"
NCBI_EMAIL = "psdehal@gmail.com"


def clean_title(t: str) -> str:
    """Strip HTML tags and extra whitespace."""
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def title_hash(t: str) -> str:
    return hashlib.sha1(t.encode()).hexdigest()[:12]


def europe_pmc_title_search(title: str, year: int | None = None) -> tuple[str, str]:
    """Search Europe PMC by title. Returns (pmid, journal_or_empty)."""
    # Strip HTML, build a TITLE: query
    clean = clean_title(title)
    # Cap title at first ~200 chars for query
    q = f'TITLE:"{clean[:200]}"'
    if year:
        q += f" AND PUB_YEAR:{year}"
    try:
        r = requests.get(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            params={"query": q, "format": "json", "resultType": "lite", "pageSize": 5},
            timeout=20,
        )
        if not r.ok:
            return ("", "")
        results = r.json().get("resultList", {}).get("result", [])
        if not results:
            return ("", "")
        # Take first result that has a pmid
        for rec in results:
            pmid = rec.get("pmid") or rec.get("id")  # both fields
            if pmid and pmid.isdigit():
                return (pmid, rec.get("journalTitle") or rec.get("journalInfo", {}).get("journal", {}).get("title", ""))
    except requests.RequestException:
        pass
    return ("", "")


def main() -> None:
    # Load hits, restrict to training set with None pmId
    hits = pd.read_parquet(PROJECT_DATA / "fb_paperblast_hit_papers.parquet")
    hits["pmId"] = hits["pmId"].astype(str)

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

    none_hits = hits[hits["pmId"] == "None"].copy()
    none_hits = none_hits[none_hits.apply(lambda r: (r["orgId"], r["locusId"]) in training_keys, axis=1)]
    print(f"None-pmid hits in training set: {len(none_hits):,}", file=sys.stderr)

    # Unique titles (with year as tiebreaker)
    none_hits["title"] = none_hits["title"].fillna("")
    none_hits["clean_title"] = none_hits["title"].apply(clean_title)
    none_hits = none_hits[none_hits["clean_title"].str.len() > 10]
    unique = none_hits[["clean_title", "year", "journal"]].drop_duplicates(subset="clean_title")
    print(f"unique non-empty titles: {len(unique):,}", file=sys.stderr)

    # Resolve each
    resolutions = []
    n_resolved = 0
    for i, (_, row) in enumerate(unique.iterrows(), 1):
        title = row["clean_title"]
        year = int(row["year"]) if pd.notna(row["year"]) else None
        pmid, journal = europe_pmc_title_search(title, year)
        if pmid:
            n_resolved += 1
        resolutions.append({
            "title_hash": title_hash(title),
            "original_title": title[:300],
            "year": year if year else "",
            "journal": row.get("journal") or "",
            "resolved_pmid": pmid,
            "found_journal": journal,
        })
        if i % 10 == 0:
            print(f"  ...{i}/{len(unique)} (resolved {n_resolved})", file=sys.stderr)
        time.sleep(0.3)

    with open(RESOLUTIONS, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(resolutions[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(resolutions)

    print(f"\nResolved {n_resolved}/{len(unique)} ({100*n_resolved/len(unique):.1f}%)", file=sys.stderr)
    print(f"Output: {RESOLUTIONS}", file=sys.stderr)


if __name__ == "__main__":
    main()
