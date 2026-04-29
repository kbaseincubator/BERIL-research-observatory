"""
Second pass title→PMID resolution with a relaxed Europe PMC search.

The first pass (notebook 46) used a strict `TITLE:"..."` query and resolved
35/122. This pass tries the still-unresolved titles with three escalating
strategies:

  1. Full-text query (no field prefix) of the cleaned title
  2. First 12 words of the title as a keyword query
  3. Title without trailing subtitle (everything after a colon dropped)

Each candidate is verified by token-Jaccard overlap (>=0.6) against our
input title before accepting the PMID.

Output:
  data/codex_summaries_titlesearch/title_resolutions_relaxed.tsv
  (Same schema as title_resolutions.tsv plus a 'strategy' column)
"""
from __future__ import annotations

import csv
import hashlib
import re
import sys
import time
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
TS_DIR = PROJECT_DATA / "codex_summaries_titlesearch"
INPUT_TSV = TS_DIR / "title_resolutions.tsv"
OUTPUT_TSV = TS_DIR / "title_resolutions_relaxed.tsv"

NCBI_EMAIL = "psdehal@gmail.com"


def clean_title(t: str) -> str:
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"&[a-z]+;", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def title_hash(t: str) -> str:
    return hashlib.sha1(t.encode()).hexdigest()[:12]


def tokenize(t: str) -> set[str]:
    """Lowercase word tokens, length >= 3."""
    words = re.findall(r"[a-z0-9]+", t.lower())
    return {w for w in words if len(w) >= 3}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def search_epmc(query: str, year: int | None = None, page_size: int = 5) -> list[dict]:
    if year:
        query = f"{query} AND PUB_YEAR:{year}"
    try:
        r = requests.get(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            params={"query": query, "format": "json", "resultType": "lite", "pageSize": page_size},
            timeout=20,
        )
        if not r.ok:
            return []
        return r.json().get("resultList", {}).get("result", [])
    except requests.RequestException:
        return []


def best_match(input_title: str, candidates: list[dict], min_jaccard: float = 0.6) -> tuple[str, str, float]:
    """Pick the candidate with highest title-jaccard >= min_jaccard. Returns (pmid, found_journal, jaccard)."""
    in_tok = tokenize(input_title)
    best = ("", "", 0.0)
    for rec in candidates:
        cand_title = clean_title(rec.get("title") or "")
        if not cand_title:
            continue
        j = jaccard(in_tok, tokenize(cand_title))
        if j >= min_jaccard and j > best[2]:
            pmid = rec.get("pmid") or ""
            if pmid and pmid.isdigit():
                journal = rec.get("journalTitle") or ""
                best = (pmid, journal, j)
    return best


def resolve_one(input_title: str, year: int | None) -> tuple[str, str, str, float]:
    """Returns (pmid, found_journal, strategy_used, jaccard)."""
    cleaned = clean_title(input_title)

    # Strategy 1: full-text query (quoted, no field prefix)
    cand = search_epmc(f'"{cleaned[:200]}"', year)
    pmid, journal, j = best_match(cleaned, cand)
    if pmid:
        return (pmid, journal, "fulltext_quoted", j)

    # Strategy 2: first 12 words as keyword query
    words = cleaned.split()
    if len(words) >= 6:
        kw_query = " ".join(words[:12])
        cand = search_epmc(kw_query, year)
        pmid, journal, j = best_match(cleaned, cand)
        if pmid:
            return (pmid, journal, "first12words", j)

    # Strategy 3: drop subtitle (everything after colon)
    if ":" in cleaned:
        head = cleaned.split(":", 1)[0].strip()
        if len(head) > 20:
            cand = search_epmc(f'TITLE:"{head}"', year)
            pmid, journal, j = best_match(cleaned, cand)
            if pmid:
                return (pmid, journal, "subtitle_drop", j)

    return ("", "", "", 0.0)


def main() -> None:
    # Load already-resolved + still-unresolved
    rows = []
    with open(INPUT_TSV) as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            rows.append(r)
    unresolved = [r for r in rows if not r.get("resolved_pmid")]
    print(f"unresolved from strict pass: {len(unresolved)}", file=sys.stderr)

    # Skip obvious conference proceedings
    skip_patterns = ("UEG Week", "Poster Present", "Annual Meeting", "Annual Symposium",
                     "Award Winners", "Wednesday: Poster", "Congress of",
                     "Annual Meeting February", "Annual Meeting March")
    skipped = 0
    todo = []
    for r in unresolved:
        if any(p in (r.get("original_title") or "") for p in skip_patterns):
            skipped += 1
            continue
        todo.append(r)
    print(f"  skipping {skipped} obvious conference proceedings", file=sys.stderr)
    print(f"  attempting relaxed resolution for {len(todo)} titles", file=sys.stderr)

    out_rows = list(rows)  # carry over already-resolved
    n_new = 0
    by_strategy: dict[str, int] = {}
    for i, r in enumerate(todo, 1):
        title = r["original_title"]
        year = int(r["year"]) if r["year"] and str(r["year"]).isdigit() else None
        pmid, journal, strategy, j = resolve_one(title, year)
        if pmid:
            n_new += 1
            by_strategy[strategy] = by_strategy.get(strategy, 0) + 1
            # Update the row in out_rows (we kept references? no, copies)
            # Find by title_hash and update
            for or_ in out_rows:
                if or_["title_hash"] == r["title_hash"]:
                    or_["resolved_pmid"] = pmid
                    or_["found_journal"] = journal
                    or_["strategy"] = strategy
                    break
        else:
            # Still unresolved — note it
            for or_ in out_rows:
                if or_["title_hash"] == r["title_hash"]:
                    or_.setdefault("strategy", "")
                    break
        if i % 10 == 0:
            print(f"  ...{i}/{len(todo)} (newly resolved: {n_new}, by strategy: {by_strategy})", file=sys.stderr)
        time.sleep(0.4)

    # Make sure all rows have a 'strategy' field
    for or_ in out_rows:
        or_.setdefault("strategy", "strict" if or_.get("resolved_pmid") else "")

    fieldnames = list(out_rows[0].keys())
    with open(OUTPUT_TSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        w.writerows(out_rows)
    n_total = sum(1 for r in out_rows if r.get("resolved_pmid"))
    print(f"\nNewly resolved: {n_new}", file=sys.stderr)
    print(f"Total resolved (strict + relaxed): {n_total} / {len(out_rows)}", file=sys.stderr)
    print(f"Output: {OUTPUT_TSV}", file=sys.stderr)


if __name__ == "__main__":
    main()
