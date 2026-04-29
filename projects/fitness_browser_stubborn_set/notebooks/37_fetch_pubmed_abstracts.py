"""
Fetch PubMed abstracts (via NCBI efetch) for papers that have no PMC version.
Used as a fallback when PMC full text is unavailable — the abstract is a
real curated summary and is sufficient for many homolog-function inferences.

Output:
  data/codex_summaries_abstracts/abstracts/<pmid>.txt   — plain abstract text
  data/codex_summaries_abstracts/abstract_index.tsv     — pmId, has_abstract
  data/codex_summaries_abstracts/tasks.jsonl            — copied from gapfill,
                                                          filtered to no-PMC pmids

Polite NCBI usage: 5 concurrent workers, tool/email param, retry on 429/5xx.
"""
from __future__ import annotations

import csv
import json
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
GAPFILL_TASKS = PROJECT_DATA / "codex_summaries_gapfill" / "tasks.jsonl"
GAPFILL_PMC_INDEX = PROJECT_DATA / "codex_summaries_gapfill" / "pmc_index.tsv"
OUT_DIR = PROJECT_DATA / "codex_summaries_abstracts"
ABSTRACT_DIR = OUT_DIR / "abstracts"
INDEX = OUT_DIR / "abstract_index.tsv"
OUT_TASKS = OUT_DIR / "tasks.jsonl"

NCBI_TOOL = "kbase-fb-stubborn"
NCBI_EMAIL = "psdehal@gmail.com"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def fetch_abstract(pmid: str) -> str:
    """Return the abstract plain text, or '' if none/failure."""
    params = {
        "db": "pubmed",
        "id": pmid,
        "rettype": "abstract",
        "retmode": "xml",
        "tool": NCBI_TOOL,
        "email": NCBI_EMAIL,
    }
    for attempt in range(4):
        try:
            r = requests.get(EFETCH_URL, params=params, timeout=30)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            try:
                root = ET.fromstring(r.text)
                # Article title + abstract
                title_elem = root.find(".//ArticleTitle")
                title = "".join(title_elem.itertext()).strip() if title_elem is not None else ""
                abstract_parts = []
                for ab in root.findall(".//Abstract/AbstractText"):
                    label = ab.get("Label", "")
                    text = "".join(ab.itertext()).strip()
                    if label:
                        abstract_parts.append(f"{label}: {text}")
                    else:
                        abstract_parts.append(text)
                abstract = "\n".join(abstract_parts).strip()
                if not abstract:
                    return ""
                return f"TITLE: {title}\n\nABSTRACT:\n{abstract}"
            except ET.ParseError:
                return ""
        except requests.RequestException:
            time.sleep(2 ** attempt)
    return ""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ABSTRACT_DIR.mkdir(parents=True, exist_ok=True)

    # Identify pmids needing abstracts: in gapfill tasks but NOT in PMC index
    have_pmc: set[str] = set()
    with open(GAPFILL_PMC_INDEX) as fh:
        next(fh)
        for line in fh:
            parts = line.split("\t")
            if len(parts) >= 3 and parts[2].strip() == "1":
                have_pmc.add(parts[0])

    needed: list[dict] = []
    with open(GAPFILL_TASKS) as fh:
        for line in fh:
            t = json.loads(line)
            if t["pmId"] not in have_pmc:
                needed.append(t)
    print(f"Papers needing abstract fetch: {len(needed):,}", file=sys.stderr)

    # Filter to ones we don't have abstracts for yet
    todo = [t for t in needed if not (ABSTRACT_DIR / f"{t['pmId']}.txt").exists()]
    print(f"  already cached: {len(needed) - len(todo):,}", file=sys.stderr)
    print(f"  to fetch:       {len(todo):,}", file=sys.stderr)

    # Write filtered tasks for downstream summarization
    with open(OUT_TASKS, "w") as fh:
        for t in needed:
            fh.write(json.dumps(t, ensure_ascii=False) + "\n")
    print(f"  wrote {OUT_TASKS}", file=sys.stderr)

    # Fetch
    fetched = 0
    failed = 0
    index_rows: list[tuple[str, int]] = []
    with ThreadPoolExecutor(max_workers=5) as ex:
        futs = {ex.submit(fetch_abstract, t["pmId"]): t["pmId"] for t in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            pmid = futs[fut]
            text = fut.result()
            if text:
                (ABSTRACT_DIR / f"{pmid}.txt").write_text(text)
                fetched += 1
            else:
                failed += 1
            if i % 50 == 0:
                print(f"  ...{i}/{len(todo)} (fetched {fetched}, failed {failed})", file=sys.stderr)

    # Build index for ALL needed (not just todo) — include cached + newly fetched
    with open(INDEX, "w") as fh:
        fh.write("pmId\thas_abstract\n")
        for t in needed:
            pmid = t["pmId"]
            has = 1 if (ABSTRACT_DIR / f"{pmid}.txt").exists() else 0
            fh.write(f"{pmid}\t{has}\n")
    print(f"\nFetched: {fetched}, Failed: {failed}", file=sys.stderr)
    have_now = sum(1 for t in needed if (ABSTRACT_DIR / f"{t['pmId']}.txt").exists())
    print(f"Total abstracts available: {have_now}/{len(needed)}", file=sys.stderr)


if __name__ == "__main__":
    main()
